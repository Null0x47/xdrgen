from __future__ import annotations

import json

import pytest

from models import (
    CloudAppEvents,
    EmailAttachmentInfo,
    EmailEvents,
    EmailPostDeliveryEvents,
    EmailUrlInfo,
    EntraIdSignInEvents,
    EntraIdSpnSignInEvents,
    GraphApiAuditEvents,
    IdentityAccountInfo,
    IdentityDirectoryEvents,
    IdentityEvents,
    IdentityLogonEvents,
    IdentityQueryEvents,
    UrlClickEvents,
)
from generators import GENERATORS
from generators.cloud_app_events import generate as generate_cae
from generators.email_attachment_info import generate as generate_email_attachment
from generators.email_corpus import corpus_for
from generators.email_events import generate as generate_email_events
from generators.email_post_delivery_events import (
    generate as generate_email_post_delivery,
)
from generators.email_url_info import generate as generate_email_url
from generators.entra_id_sign_in_events import generate as generate_signin
from generators.entra_id_spn_sign_in_events import (
    _SERVICE_PRINCIPALS,
    generate as generate_spn,
)
from generators.graph_api_audit_events import (
    _ENDPOINTS as GRAPH_ENDPOINTS,
    _STATUS_VALUES as GRAPH_STATUS_VALUES,
    generate as generate_graph_api,
)
from generators.identity_account_info import generate as generate_account_info
from generators.identity_directory_events import generate as generate_directory
from generators.identity_events import generate as generate_identity
from generators.identity_logon_events import generate as generate_logon
from generators.identity_query_events import generate as generate_query
from generators.url_click_events import generate as generate_url_click
from world import World

# Snapshot the defaults from a fresh World once for compactness in the
# many tests that just want to assert "the generated event reflects the
# default fixtures". Tests that exercise overrides build their own World.
_DEFAULTS = None  # populated below


def _refs():
    global _DEFAULTS
    if _DEFAULTS is None:
        _w = World()
        _DEFAULTS = {
            "TENANT_ID": _w.tenant_id,
            "ON_PREM_AD_DOMAIN": _w.on_prem_ad_domain,
            "ON_PREM_SID_PREFIX": _w.on_prem_sid_prefix,
            "DOMAIN_CONTROLLERS": [
                {"name": dc.name, "ip": dc.ip} for dc in _w.domain_controllers
            ],
            "IPS": [{"ip": i.ip, "category": i.category} for i in _w.ips],
            "USERS": [
                {"upn": u.upn, "type": u.type, "sam_account_name": u.sam_account_name}
                for u in _w.users
            ],
        }
    return _DEFAULTS


TENANT_ID = _refs()["TENANT_ID"]
ON_PREM_AD_DOMAIN = _refs()["ON_PREM_AD_DOMAIN"]
ON_PREM_SID_PREFIX = _refs()["ON_PREM_SID_PREFIX"]
DOMAIN_CONTROLLERS = _refs()["DOMAIN_CONTROLLERS"]
IPS = _refs()["IPS"]
USERS = _refs()["USERS"]


@pytest.fixture(scope="session")
def _world() -> World:
    """Shared default World for tests that exercise the registry contract."""
    return World()


def test_generators_registry_lists_every_supported_table():
    assert set(GENERATORS) == {
        "CloudAppEvents",
        "EmailAttachmentInfo",
        "EmailEvents",
        "EmailPostDeliveryEvents",
        "EmailUrlInfo",
        "EntraIdSignInEvents",
        "EntraIdSpnSignInEvents",
        "GraphApiAuditEvents",
        "IdentityAccountInfo",
        "IdentityDirectoryEvents",
        "IdentityEvents",
        "IdentityLogonEvents",
        "IdentityQueryEvents",
        "UrlClickEvents",
    }


def test_cloud_app_events_round_trips_through_model(_world):
    event = generate_cae(_world)

    assert isinstance(event, CloudAppEvents)
    payload = event.model_dump_json(by_alias=True)
    # Re-validating proves every field type matches the schema.
    CloudAppEvents.model_validate_json(payload)


def test_cloud_app_events_uses_known_user_and_ip(_world):
    event = generate_cae(_world)

    user_upns = {u["upn"] for u in USERS}
    ips = {i["ip"] for i in IPS}
    assert event.AccountId in user_upns
    assert event.IPAddress in ips
    assert event.TenantId == TENANT_ID


def test_cloud_app_events_action_drives_object_type(_world):
    # Run enough samples that we hit each action category at least once.
    seen_types: set[str] = set()
    for _ in range(200):
        event = generate_cae(_world)
        seen_types.add(event.ObjectType)
        action = event.ActionType.lower()
        if "file" in action or action.startswith("git."):
            assert event.ObjectType == "File"
        if "login" in action or "logout" in action:
            assert event.ObjectType == "Account"

    # The pool covers multiple object types — confirm we aren't always the same.
    assert len(seen_types) >= 2


def test_cloud_app_events_external_user_flag_matches_upn(_world):
    for _ in range(100):
        event = generate_cae(_world)
        assert event.IsExternalUser == ("#EXT#" in event.AccountId)


def test_entra_id_sign_in_events_round_trips_through_model(_world):
    event = generate_signin(_world)

    assert isinstance(event, EntraIdSignInEvents)
    EntraIdSignInEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_entra_id_sign_in_events_conditional_access_is_valid_json(_world):
    event = generate_signin(_world)

    parsed = json.loads(event.ConditionalAccessPolicies)
    assert isinstance(parsed, list)
    assert all("id" in p and "displayName" in p for p in parsed)


def test_entra_id_sign_in_events_application_account_is_non_interactive(_world):
    # Force-pick the Application user by sampling many events and checking the
    # invariant whenever we hit them.
    saw_app_user = False
    for _ in range(500):
        event = generate_signin(_world)
        # The Application-typed user has display_name 'svc-deploy'.
        if event.AccountDisplayName == "svc-deploy":
            saw_app_user = True
            assert event.LogonType == "nonInteractiveUser"
            assert event.IsConfidentialClient is True
    assert saw_app_user, "expected Application-typed user to be picked at least once"


def test_entra_id_sign_in_events_guest_flag_matches_upn(_world):
    for _ in range(100):
        event = generate_signin(_world)
        is_ext = "#EXT#" in event.AccountUpn
        assert event.IsExternalUser == (1 if is_ext else 0)
        assert event.IsGuestUser == is_ext


def test_entra_id_spn_sign_in_events_round_trips_through_model(_world):
    event = generate_spn(_world)

    assert isinstance(event, EntraIdSpnSignInEvents)
    EntraIdSpnSignInEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_entra_id_spn_sign_in_events_managed_identity_uses_cloud_provider_ip(_world):
    cloud_ips = {i["ip"] for i in IPS if i["category"] == "Cloud provider"}
    mi_names = {sp["name"] for sp in _SERVICE_PRINCIPALS if sp["is_managed_identity"]}

    saw_mi = False
    for _ in range(500):
        event = generate_spn(_world)
        if event.ServicePrincipalName in mi_names:
            saw_mi = True
            assert event.IsManagedIdentity is True
            assert event.IPAddress in cloud_ips
    assert saw_mi, "expected managed identity SPN to be picked at least once"


def test_entra_id_spn_sign_in_events_resource_tenant_matches_common(_world):
    event = generate_spn(_world)

    assert event.ResourceTenantId == TENANT_ID


def test_entra_id_sign_in_error_codes_drawn_from_world_catalogue(_world):
    valid_codes = {c.code for c in _world.entra_sign_in_error_codes}
    seen: set[int] = set()
    for _ in range(500):
        event = generate_signin(_world)
        assert event.ErrorCode in valid_codes
        seen.add(event.ErrorCode)
    # The expanded default list should yield several distinct codes across
    # 500 samples; if we ever only see success the weights got broken.
    assert len(seen) >= 3


def test_entra_id_sign_in_error_codes_override_constrains_distribution():
    """When the YAML pins a single failure code with weight 1, every emitted
    event must carry exactly that code — proves the override actually flows
    through into the generator instead of getting silently ignored."""
    from world import Overrides, Profile, WeightedErrorCode

    prof = Profile(
        tables=["EntraIdSignInEvents"],
        overrides=Overrides(
            entra_sign_in_error_codes=[
                WeightedErrorCode(
                    code=50126,
                    weight=1,
                    description="InvalidUserNameOrPassword",
                )
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_signin(world)
        assert event.ErrorCode == 50126
        # Description from the override flows into AuthenticationProcessingDetails.
        assert event.AuthenticationProcessingDetails == "InvalidUserNameOrPassword"


def test_entra_id_spn_sign_in_error_codes_override_constrains_distribution():
    from world import Overrides, Profile, WeightedErrorCode

    prof = Profile(
        tables=["EntraIdSpnSignInEvents"],
        overrides=Overrides(
            entra_spn_sign_in_error_codes=[WeightedErrorCode(code=7000222, weight=1)]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_spn(world)
        assert event.ErrorCode == 7000222


def test_identity_logon_events_round_trips_through_model(_world):
    event = generate_logon(_world)

    assert isinstance(event, IdentityLogonEvents)
    IdentityLogonEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_identity_logon_events_terminate_at_a_known_dc(_world):
    dc_names = {dc["name"] for dc in DOMAIN_CONTROLLERS}
    dc_ips = {dc["ip"] for dc in DOMAIN_CONTROLLERS}
    for _ in range(50):
        event = generate_logon(_world)
        assert event.DestinationDeviceName in dc_names
        assert event.DestinationIPAddress in dc_ips
        assert event.AccountDomain == ON_PREM_AD_DOMAIN


def test_identity_logon_events_failure_reason_only_set_on_failure(_world):
    saw_failure = False
    for _ in range(500):
        event = generate_logon(_world)
        if event.ActionType == "LogonFailed":
            saw_failure = True
            assert event.FailureReason is not None
        else:
            assert event.ActionType == "LogonSuccess"
            assert event.FailureReason is None
    assert saw_failure, "expected at least one LogonFailed in 500 samples"


def test_identity_query_events_round_trips_through_model(_world):
    event = generate_query(_world)

    assert isinstance(event, IdentityQueryEvents)
    IdentityQueryEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_identity_query_events_protocol_matches_destination_port(_world):
    expected = {
        "Ldap": "389",
        "Samr": "445",
        "Dns": "53",
    }
    for _ in range(100):
        event = generate_query(_world)
        assert event.DestinationPort == expected[event.Protocol]


def test_identity_query_events_action_type_includes_protocol(_world):
    for _ in range(50):
        event = generate_query(_world)
        assert event.Protocol in event.ActionType


def test_identity_directory_events_round_trips_through_model(_world):
    event = generate_directory(_world)

    assert isinstance(event, IdentityDirectoryEvents)
    IdentityDirectoryEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_identity_directory_events_actor_and_target_are_known_users(_world):
    upns = {u["upn"] for u in USERS}
    for _ in range(50):
        event = generate_directory(_world)
        assert event.AccountUpn in upns
        assert event.TargetAccountUpn in upns
        assert event.AccountDomain == ON_PREM_AD_DOMAIN


def test_identity_events_round_trips_through_model(_world):
    event = generate_identity(_world)

    assert isinstance(event, IdentityEvents)
    IdentityEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_identity_events_action_result_matches_action_type(_world):
    saw_failure = False
    for _ in range(500):
        event = generate_identity(_world)
        if "Failed" in event.ActionType or "fail" in event.ActionType.lower():
            saw_failure = True
            assert event.ActionResult == "Failure"
            assert event.ActionFailureReason is not None
        else:
            assert event.ActionResult == "Success"
            assert event.ActionFailureReason is None
    assert saw_failure, "expected at least one failed ActionType in 500 samples"


def test_identity_events_target_objects_is_a_non_empty_list(_world):
    for _ in range(50):
        event = generate_identity(_world)
        assert isinstance(event.TargetObjects, list)
        assert len(event.TargetObjects) >= 1
        for t in event.TargetObjects:
            assert {"Type", "Name", "Id"}.issubset(t.keys())


def test_identity_account_info_round_trips_through_model(_world):
    event = generate_account_info(_world)

    assert isinstance(event, IdentityAccountInfo)
    IdentityAccountInfo.model_validate_json(event.model_dump_json(by_alias=True))


def test_identity_account_info_admin_carries_sensitive_tag(_world):
    admin_upns = {u["upn"] for u in USERS if u["type"] == "Admin"}
    saw_admin = False
    for _ in range(500):
        event = generate_account_info(_world)
        if event.AccountUpn in admin_upns:
            saw_admin = True
            assert "Sensitive" in event.Tags
            assert event.CriticalityLevel == 4
    assert saw_admin, "expected admin user to appear at least once"


def test_identity_account_info_service_account_has_no_mfa(_world):
    service_upns = {u["upn"] for u in USERS if u["type"] == "Application"}
    saw_service = False
    for _ in range(500):
        event = generate_account_info(_world)
        if event.AccountUpn in service_upns:
            saw_service = True
            assert event.Type == "ServiceAccount"
            assert event.EnrolledMfas == []
    assert saw_service, "expected service account user to appear at least once"


def test_identity_account_info_sid_uses_shared_prefix_when_present(_world):
    for _ in range(50):
        event = generate_account_info(_world)
        if event.Sid is not None:
            assert event.Sid.startswith(ON_PREM_SID_PREFIX + "-")


@pytest.fixture(scope="session")
def _corpus(_world):
    return corpus_for(_world)


@pytest.fixture(scope="session")
def _pool_nm_ids(_corpus):
    return {e["network_message_id"] for e in _corpus.entries}


@pytest.fixture(scope="session")
def _pool_nm_ids_with_attachments(_corpus):
    return {e["network_message_id"] for e in _corpus.entries if e["attachments"]}


@pytest.fixture(scope="session")
def _pool_nm_ids_with_urls(_corpus):
    return {e["network_message_id"] for e in _corpus.entries if e["urls"]}


@pytest.fixture(scope="session")
def _phish_nm_ids(_corpus):
    return {e["network_message_id"] for e in _corpus.entries if e["threat_types"]}


def test_email_events_round_trips_through_model(_world):
    event = generate_email_events(_world)

    assert isinstance(event, EmailEvents)
    EmailEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_email_attachment_info_round_trips_through_model(_world):
    event = generate_email_attachment(_world)

    assert isinstance(event, EmailAttachmentInfo)
    EmailAttachmentInfo.model_validate_json(event.model_dump_json(by_alias=True))


def test_email_post_delivery_events_round_trips_through_model(_world):
    event = generate_email_post_delivery(_world)

    assert isinstance(event, EmailPostDeliveryEvents)
    EmailPostDeliveryEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_email_url_info_round_trips_through_model(_world):
    event = generate_email_url(_world)

    assert isinstance(event, EmailUrlInfo)
    EmailUrlInfo.model_validate_json(event.model_dump_json(by_alias=True))


def test_url_click_events_round_trips_through_model(_world):
    event = generate_url_click(_world)

    assert isinstance(event, UrlClickEvents)
    UrlClickEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_every_email_table_uses_a_pool_network_message_id(
    _world,
    _pool_nm_ids,
    _pool_nm_ids_with_attachments,
    _pool_nm_ids_with_urls,
):
    """Each Email* / UrlClickEvents row must reference a NetworkMessageId
    from the shared corpus — that is the property that lets an analyst
    pivot from any one row to every related row."""
    for _ in range(50):
        assert generate_email_events(_world).NetworkMessageId in _pool_nm_ids
        assert generate_email_post_delivery(_world).NetworkMessageId in _pool_nm_ids
        assert generate_email_url(_world).NetworkMessageId in _pool_nm_ids_with_urls
        assert (
            generate_email_attachment(_world).NetworkMessageId
            in _pool_nm_ids_with_attachments
        )
        assert generate_url_click(_world).NetworkMessageId in _pool_nm_ids_with_urls


def test_email_attachment_info_carries_attachment_specific_fields(_world):
    for _ in range(50):
        event = generate_email_attachment(_world)
        assert event.FileName
        assert event.FileExtension
        assert event.FileSize and event.FileSize > 0
        # SHA-256 is hex-encoded 64 chars.
        assert event.SHA256 and len(event.SHA256) == 64
        int(event.SHA256, 16)


def test_email_correlation_holds_across_tables(_world, _corpus):
    """The correlation invariant: across a mixed stream of Email* /
    UrlClickEvents events, the same NetworkMessageId appears in at least
    two different tables. With a pool of 8 emails and 5 generators, after
    ~250 samples this is overwhelmingly likely."""
    by_nm_id: dict[str, set[str]] = {}
    for _ in range(60):
        for table in (
            "EmailEvents",
            "EmailAttachmentInfo",
            "EmailPostDeliveryEvents",
            "EmailUrlInfo",
            "UrlClickEvents",
        ):
            event = GENERATORS[table](_world)
            by_nm_id.setdefault(event.NetworkMessageId, set()).add(table)

    multi_table_ids = {
        nm: tables for nm, tables in by_nm_id.items() if len(tables) >= 2
    }
    assert multi_table_ids, (
        "expected at least one NetworkMessageId to appear in >= 2 tables — "
        "this is the whole point of pivot-by-NetworkMessageId"
    )
    # And in fact most pool entries should pivot across all five tables given
    # how often we sample. Loosely require half the pool to multi-pivot.
    assert len(multi_table_ids) >= len(_corpus.entries) // 2


def test_email_post_delivery_for_phish_uses_admin_or_zap_trigger(_world, _phish_nm_ids):
    """When the underlying email already carries a phishing verdict, the
    post-delivery action must come from ZAP or an admin — a user can't
    'Move to inbox' on something that was quarantined as phish."""
    saw_phish = False
    for _ in range(500):
        event = generate_email_post_delivery(_world)
        if event.NetworkMessageId in _phish_nm_ids:
            saw_phish = True
            assert event.ActionTrigger in ("ZAP", "Admin")
    assert saw_phish, "expected the phishing email to be sampled at least once"


def test_url_click_recipient_matches_email_recipient(_world, _corpus):
    """The clicker has to be the email's recipient — UrlClickEvents joins
    EmailEvents on (NetworkMessageId, AccountUpn)."""
    nm_to_recipient = {
        e["network_message_id"]: e["recipient"].upn for e in _corpus.entries
    }
    for _ in range(50):
        event = generate_url_click(_world)
        assert event.AccountUpn == nm_to_recipient[event.NetworkMessageId]


def test_url_click_phish_email_blocks_the_click(_world, _phish_nm_ids):
    """A click into a known-phish email must surface as a Blockpage / not
    clicked-through outcome regardless of the random outcome roll."""
    saw_phish = False
    for _ in range(500):
        event = generate_url_click(_world)
        if event.NetworkMessageId in _phish_nm_ids:
            saw_phish = True
            assert event.ActionType in (
                "Blockpage",
                "ClickBlocked",
                "BlockpageOverride",
            )
    assert saw_phish, "expected the phishing email to be sampled at least once"


def test_graph_api_audit_events_round_trips_through_model(_world):
    event = generate_graph_api(_world)

    assert isinstance(event, GraphApiAuditEvents)
    GraphApiAuditEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_graph_api_audit_events_uses_world_identity(_world):
    """IdentityProvider must reference the world tenant, the IP must come
    from the world IP pool, and the application must be a known client app."""
    app_ids = {a.app_id for a in _world.client_apps}
    ip_pool = {i.ip for i in _world.ips}
    for _ in range(50):
        event = generate_graph_api(_world)
        assert event.IdentityProvider == f"https://sts.windows.net/{_world.tenant_id}/"
        assert event.IPAddress in ip_pool
        assert event.ApplicationId in app_ids
        assert event.ServicePrincipalId in app_ids


def test_graph_api_audit_events_request_uri_is_well_formed(_world):
    valid_methods = {"GET", "POST", "PATCH", "DELETE"}
    valid_versions = ("v1.0", "beta")
    for _ in range(50):
        event = generate_graph_api(_world)
        assert event.RequestUri.startswith("https://graph.microsoft.com/")
        assert event.RequestMethod in valid_methods
        assert event.ApiVersion in valid_versions
        # API version embedded in the URI matches the ApiVersion column.
        assert f"/{event.ApiVersion}/" in event.RequestUri
        # No template placeholders escaped into output.
        assert "{" not in event.RequestUri
        assert "}" not in event.RequestUri


def test_graph_api_audit_events_status_codes_drawn_from_known_set(_world):
    valid_status = set(GRAPH_STATUS_VALUES)
    valid_workloads = {e["workload"] for e in GRAPH_ENDPOINTS}
    for _ in range(50):
        event = generate_graph_api(_world)
        assert event.ResponseStatusCode in valid_status
        assert event.TargetWorkload in valid_workloads


def test_graph_api_audit_events_delegated_vs_app_only_shape(_world):
    """Delegated calls (EntityType=User) must populate AccountObjectId from
    the world user pool. App-only calls (EntityType=ServicePrincipal) must
    leave AccountObjectId empty — that's how real Graph audit rows separate
    the two flows."""
    user_oids = {u.object_id for u in _world.users}
    saw_user = saw_sp = False
    for _ in range(200):
        event = generate_graph_api(_world)
        if event.EntityType == "User":
            saw_user = True
            assert event.AccountObjectId in user_oids
        else:
            assert event.EntityType == "ServicePrincipal"
            saw_sp = True
            assert event.AccountObjectId is None
    assert saw_user, "expected at least one delegated (User) call across 200 samples"
    assert saw_sp, (
        "expected at least one app-only (ServicePrincipal) call across 200 samples"
    )


def test_graph_api_audit_events_group_uri_uses_world_group_pool(_world):
    """When the URI carries a `/groups/<id>/...` path, the id must come
    from `world.groups`, not a freshly-minted UUID."""
    valid_group_ids = {g.id for g in _world.groups}
    saw_group_uri = False
    for _ in range(500):
        event = generate_graph_api(_world)
        marker = "/groups/"
        if marker in event.RequestUri and "/groups/$ref" not in event.RequestUri:
            tail = event.RequestUri.split(marker, 1)[1]
            group_id = tail.split("/", 1)[0]
            if group_id and group_id != "":
                saw_group_uri = True
                assert group_id in valid_group_ids
    assert saw_group_uri, "expected at least one /groups/<id>/... URI in 500 samples"


def test_graph_api_audit_events_group_override_constrains_uri():
    from world import Group, Overrides, Profile

    prof = Profile(
        tables=["GraphApiAuditEvents"],
        overrides=Overrides(
            groups=[Group(name="Only Group", id="00000000-1111-2222-3333-444444444444")]
        ),
    )
    world = prof.build_world()
    saw_group_uri = False
    for _ in range(500):
        event = generate_graph_api(world)
        if "/groups/" in event.RequestUri and "/groups/$ref" not in event.RequestUri:
            tail = event.RequestUri.split("/groups/", 1)[1]
            group_id = tail.split("/", 1)[0]
            if group_id:
                saw_group_uri = True
                assert group_id == "00000000-1111-2222-3333-444444444444"
    assert saw_group_uri, "expected the group endpoint to be exercised"


def test_graph_api_audit_events_204_has_zero_response_size(_world):
    """A 204 No Content response, by definition, returns zero body bytes —
    catch the day someone wires up a non-zero default for it."""
    for _ in range(500):
        event = generate_graph_api(_world)
        if event.ResponseStatusCode == "204":
            assert event.ResponseSize == 0


def test_world_overrides_propagate_into_generated_events():
    """A user-supplied tenant_id / tenant_domain in the YAML config must
    show up on every generated event — that's the whole point of overrides.

    Replaces the older `apply_overrides` mutation test: the contract is now
    "build a World, pass it to the generator, the values surface" — no
    module-level state involved."""
    from world import Overrides, Profile

    prof = Profile(
        tables=["IdentityLogonEvents"],
        overrides=Overrides(
            tenant_id="99999999-aaaa-bbbb-cccc-dddddddddddd",
            tenant_domain="northwind.com",
            on_prem_ad_domain="northwind.local",
            on_prem_sid_prefix="S-1-5-21-1-2-3",
        ),
    )
    world = prof.build_world()

    evt = generate_logon(world)
    assert evt.TenantId == "99999999-aaaa-bbbb-cccc-dddddddddddd"
    assert evt.AccountDomain == "northwind.local"
    if evt.AccountSid:
        assert evt.AccountSid.startswith("S-1-5-21-1-2-3-")


def test_overrides_rejects_unknown_keys():
    """Pydantic catches unknown keys at validation time."""
    from pydantic import ValidationError

    from world import Overrides

    with pytest.raises(ValidationError):
        Overrides.model_validate({"not_a_real_key": "x"})


def test_world_overrides_replace_collections_for_subsequent_events():
    """All collection overrides on `Overrides` must show up on the next
    generated event — replaces the legacy in-place-mutation test."""
    from world import Overrides, Profile

    prof = Profile(
        tables=["EntraIdSignInEvents"],
        overrides=Overrides.model_validate(
            {
                "domain_controllers": [
                    {
                        "name": "DC-NW-01.northwind.local",
                        "ip": "10.10.0.10",
                        "device_id": "ffffffff-1111-2222-3333-444444444444",
                    }
                ],
                "users": [
                    {
                        "display_name": "Lonely Admin",
                        "upn": "lonely.admin@northwind.com",
                        "object_id": "11111111-2222-3333-4444-555555555555",
                        "type": "Admin",
                        "sam_account_name": "lonely.admin",
                        "sid_rid": 500,
                    }
                ],
                "ips": [
                    {
                        "ip": "9.9.9.9",
                        "city": "Test",
                        "state": "Test",
                        "country": "ZZ",
                        "isp": "Lab",
                        "category": "Corporate",
                        "latitude": "0.0",
                        "longitude": "0.0",
                    }
                ],
                "user_agents": [
                    {
                        "ua": "TestAgent/1.0",
                        "platform": "Linux",
                        "device_type": "Workstation",
                        "browser": "TestBrowser 1.0",
                    }
                ],
                "client_apps": [
                    {
                        "name": "Custom App",
                        "app_id": "00000000-1111-2222-3333-444444444444",
                    }
                ],
                "resources": [
                    {
                        "name": "Custom Resource",
                        "id": "00000000-aaaa-bbbb-cccc-dddddddddddd",
                    }
                ],
                "conditional_access_policies": [
                    {
                        "id": "ca-policy-northwind",
                        "displayName": "Northwind: require MFA",
                        "enforcedGrantControls": ["Mfa"],
                    }
                ],
            }
        ),
    )
    world = prof.build_world()

    assert len(world.users) == 1
    assert world.users[0].upn == "lonely.admin@northwind.com"
    assert world.domain_controllers[0].name == "DC-NW-01.northwind.local"
    assert world.ips[0].ip == "9.9.9.9"
    assert world.user_agents[0].ua == "TestAgent/1.0"
    assert world.client_apps[0].name == "Custom App"
    assert world.resources[0].name == "Custom Resource"
    assert world.conditional_access_policies[0].id == "ca-policy-northwind"

    evt = generate_signin(world)
    assert evt.AccountUpn == "lonely.admin@northwind.com"
    assert evt.Application == "Custom App"
    assert evt.ResourceDisplayName == "Custom Resource"


def test_overrides_validates_user_shape():
    """Bad shapes are caught by the Pydantic User model — caller gets a
    validation error rather than the generator KeyError'ing later."""
    from pydantic import ValidationError

    from world import Overrides

    with pytest.raises(ValidationError):
        Overrides.model_validate({"users": [{"upn": "missing.fields@northwind.com"}]})


@pytest.mark.parametrize("table", sorted(GENERATORS))
def test_every_registered_generator_produces_a_valid_event(table, _world):
    event = GENERATORS[table](_world)
    # If the JSON dump round-trips, the event matches its model schema.
    payload = event.model_dump_json(by_alias=True)
    type(event).model_validate_json(payload)
