from __future__ import annotations

import json

import pytest

from models import (
    CloudAppEvents,
    DeviceEvents,
    DeviceFileCertificateInfo,
    DeviceFileEvents,
    DeviceImageLoadEvents,
    DeviceLogonEvents,
    DeviceNetworkEvents,
    DeviceNetworkInfo,
    DeviceProcessEvents,
    DeviceRegistryEvents,
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
from generators.device_events import generate as generate_device_events
from generators.device_file_certificate_info import (
    generate as generate_device_cert,
)
from generators.device_file_events import generate as generate_device_file
from generators.device_image_load_events import (
    generate as generate_device_image_load,
)
from generators.device_logon_events import generate as generate_device_logon
from generators.device_network_events import (
    generate as generate_device_network,
)
from generators.device_network_info import (
    generate as generate_device_network_info,
)
from generators.device_process_events import (
    generate as generate_device_process,
)
from generators.device_registry_events import (
    generate as generate_device_registry,
)
from generators.email_attachment_info import generate as generate_email_attachment
from generators.email_pool import pool_for
from generators.email_events import generate as generate_email_events
from generators.email_post_delivery_events import (
    generate as generate_email_post_delivery,
)
from generators.email_url_info import generate as generate_email_url
from generators.entra_id_sign_in_events import generate as generate_signin
from generators.entra_id_spn_sign_in_events import (
    generate as generate_spn,
)
from generators.graph_api_audit_events import (
    generate as generate_graph_api,
)
from generators.identity_account_info import generate as generate_account_info
from generators.identity_directory_events import generate as generate_directory
from generators.identity_events import generate as generate_identity
from generators.identity_logon_events import generate as generate_logon
from generators.identity_query_events import generate as generate_query
from generators.url_click_events import generate as generate_url_click
from world import NetworkDestination, RegistryTarget, World

# Default-World snapshot for tests that don't exercise overrides.
_DEFAULTS = None


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
    return World()


def test_generators_registry_lists_every_supported_table():
    assert set(GENERATORS) == {
        "CloudAppEvents",
        "DeviceEvents",
        "DeviceFileCertificateInfo",
        "DeviceFileEvents",
        "DeviceImageLoadEvents",
        "DeviceLogonEvents",
        "DeviceNetworkEvents",
        "DeviceNetworkInfo",
        "DeviceProcessEvents",
        "DeviceRegistryEvents",
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
    CloudAppEvents.model_validate_json(payload)


def test_cloud_app_events_uses_known_user_and_ip(_world):
    event = generate_cae(_world)

    user_upns = {u["upn"] for u in USERS}
    ips = {i["ip"] for i in IPS}
    assert event.AccountId in user_upns
    assert event.IPAddress in ips
    assert event.TenantId == TENANT_ID


def test_cloud_app_events_action_drives_object_type(_world):
    seen_types: set[str] = set()
    for _ in range(200):
        event = generate_cae(_world)
        seen_types.add(event.ObjectType)
        action = event.ActionType.lower()
        if "file" in action or action.startswith("git."):
            assert event.ObjectType == "File"
        if "login" in action or "logout" in action:
            assert event.ObjectType == "Account"

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
    saw_app_user = False
    for _ in range(500):
        event = generate_signin(_world)
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
    mi_names = {sp.name for sp in _world.service_principals if sp.is_managed_identity}

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


def test_entra_id_spn_sign_in_events_service_principals_override():
    """Profile service_principals override flows into generated rows."""
    from world import Overrides, Profile, ServicePrincipal

    prof = Profile(
        tables=["EntraIdSpnSignInEvents"],
        overrides=Overrides(
            service_principals=[
                ServicePrincipal(
                    name="northwind-only-sp",
                    id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    app_id="11111111-2222-3333-4444-555555555555",
                    is_managed_identity=False,
                )
            ]
        ),
    )
    world = prof.build_world()

    for _ in range(50):
        event = generate_spn(world)
        assert event.ServicePrincipalName == "northwind-only-sp"
        assert event.ApplicationId == "11111111-2222-3333-4444-555555555555"


def test_entra_id_spn_sign_in_events_resources_override_used_when_set():
    """`resources:` override beats the SPN generator's file-local fallback."""
    from world import Overrides, Profile, Resource

    prof = Profile(
        tables=["EntraIdSpnSignInEvents"],
        overrides=Overrides(
            resources=[
                Resource(
                    name="Northwind LOB API",
                    id="99999999-aaaa-bbbb-cccc-dddddddddddd",
                )
            ]
        ),
    )
    world = prof.build_world()

    for _ in range(50):
        event = generate_spn(world)
        assert event.ResourceDisplayName == "Northwind LOB API"
        assert event.ResourceId == "99999999-aaaa-bbbb-cccc-dddddddddddd"


def test_entra_id_spn_sign_in_events_resources_fallback_when_unset(_world):
    """No override → SPN generator uses _DEFAULT_SPN_RESOURCES, not world.resources."""
    from generators.entra_id_spn_sign_in_events import _DEFAULT_SPN_RESOURCES

    fallback_names = {r.name for r in _DEFAULT_SPN_RESOURCES}
    seen: set[str] = set()
    for _ in range(200):
        event = generate_spn(_world)
        assert event.ResourceDisplayName in fallback_names
        seen.add(event.ResourceDisplayName)
    assert len(seen) >= 3


def test_entra_id_sign_in_error_codes_drawn_from_world_catalogue(_world):
    valid_codes = {c.code for c in _world.entra_sign_in_error_codes}
    seen: set[int] = set()
    for _ in range(500):
        event = generate_signin(_world)
        assert event.ErrorCode in valid_codes
        seen.add(event.ErrorCode)
    assert len(seen) >= 3


def test_entra_id_sign_in_error_codes_override_constrains_distribution():
    """Pinning a single error code via YAML constrains every emitted event."""
    from world import Overrides, Profile, ErrorCode

    prof = Profile(
        tables=["EntraIdSignInEvents"],
        overrides=Overrides(
            entra_sign_in_error_codes=[
                ErrorCode(
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
        assert event.AuthenticationProcessingDetails == "InvalidUserNameOrPassword"


def test_entra_id_spn_sign_in_error_codes_override_constrains_distribution():
    from world import Overrides, Profile, ErrorCode

    prof = Profile(
        tables=["EntraIdSpnSignInEvents"],
        overrides=Overrides(
            entra_spn_sign_in_error_codes=[ErrorCode(code=7000222, weight=1)]
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
def _pool(_world):
    return pool_for(_world)


@pytest.fixture(scope="session")
def _pool_nm_ids(_pool):
    return {e["network_message_id"] for e in _pool.entries}


@pytest.fixture(scope="session")
def _pool_nm_ids_with_attachments(_pool):
    return {e["network_message_id"] for e in _pool.entries if e["attachments"]}


@pytest.fixture(scope="session")
def _pool_nm_ids_with_urls(_pool):
    return {e["network_message_id"] for e in _pool.entries if e["urls"]}


@pytest.fixture(scope="session")
def _phish_nm_ids(_pool):
    return {e["network_message_id"] for e in _pool.entries if e["threat_types"]}


def test_email_templates_override_replaces_pool():
    """An `email_templates:` override flows into every Email* / UrlClick row."""
    from world import EmailTemplate, EmailUrl, Overrides, Profile

    only_template = EmailTemplate(
        subject="Northwind Lab — single test mail",
        sender_display_name="Northwind Lab",
        sender_from_address="lab@northwind.com",
        sender_from_domain="northwind.com",
        sender_mail_from_address="lab@northwind.com",
        sender_mail_from_domain="northwind.com",
        recipient_persona="avery.chen",
        direction="Inbound",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=10000,
        bulk_complaint_level=0,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"-1"}',
        urls=(
            EmailUrl(
                url="https://northwind.com/lab",
                domain="northwind.com",
                location="Body",
            ),
        ),
    )
    prof = Profile(
        tables=["EmailEvents"],
        overrides=Overrides(email_templates=[only_template]),
    )
    world = prof.build_world()

    assert len(world.email_templates) == 1
    for _ in range(50):
        event = generate_email_events(world)
        assert event.Subject == "Northwind Lab — single test mail"
        assert event.SenderFromDomain == "northwind.com"


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
    """Every Email*/UrlClick row references a NetworkMessageId in the pool."""
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
        assert event.SHA256 and len(event.SHA256) == 64
        int(event.SHA256, 16)


def test_email_correlation_holds_across_tables(_world, _pool):
    """Same NetworkMessageId appears across multiple Email*/UrlClick tables."""
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
        "expected at least one NetworkMessageId to appear in >= 2 tables"
    )
    assert len(multi_table_ids) >= len(_pool.entries) // 2


def test_email_post_delivery_for_phish_uses_admin_or_zap_trigger(_world, _phish_nm_ids):
    """Phish verdicts only get ZAP / admin remediation, never user 'Move to inbox'."""
    saw_phish = False
    for _ in range(500):
        event = generate_email_post_delivery(_world)
        if event.NetworkMessageId in _phish_nm_ids:
            saw_phish = True
            assert event.ActionTrigger in ("ZAP", "Admin")
    assert saw_phish, "expected the phishing email to be sampled at least once"


def test_url_click_recipient_matches_email_recipient(_world, _pool):
    """UrlClickEvents joins EmailEvents on (NetworkMessageId, AccountUpn)."""
    nm_to_recipient = {
        e["network_message_id"]: e["recipient"].upn for e in _pool.entries
    }
    for _ in range(50):
        event = generate_url_click(_world)
        assert event.AccountUpn == nm_to_recipient[event.NetworkMessageId]


def test_url_click_phish_email_blocks_the_click(_world, _phish_nm_ids):
    """Phish-verdict emails always surface a Block* outcome regardless of roll."""
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
    """IdentityProvider/IP/app must come from the world fixtures."""
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
        assert f"/{event.ApiVersion}/" in event.RequestUri
        assert "{" not in event.RequestUri
        assert "}" not in event.RequestUri


def test_graph_api_audit_events_status_codes_drawn_from_known_set(_world):
    valid_status = {s.code for s in _world.graph_api_status_codes}
    valid_workloads = {e.workload for e in _world.graph_api_endpoints}
    for _ in range(50):
        event = generate_graph_api(_world)
        assert event.ResponseStatusCode in valid_status
        assert event.TargetWorkload in valid_workloads


def test_graph_api_audit_events_delegated_vs_app_only_shape(_world):
    """Delegated calls populate AccountObjectId; app-only calls leave it null."""
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
    """`/groups/<id>/...` URIs use `world.groups` ids, not fresh UUIDs."""
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


def test_graph_api_audit_events_endpoint_override_constrains_uri():
    """`graph_api_endpoints` override fully replaces the default catalogue
    and pre-versioned URIs pin ApiVersion to the literal in the path."""
    from world import GraphApiEndpoint, Overrides, Profile

    prof = Profile(
        tables=["GraphApiAuditEvents"],
        overrides=Overrides(
            graph_api_endpoints=[
                GraphApiEndpoint(
                    method="GET",
                    uri="/beta/devices/{device_id}/registeredOwners",
                    workload="Microsoft.DirectoryServices",
                    scope="Device.Read.All",
                ),
                GraphApiEndpoint(
                    method="GET",
                    uri="/v1.0/organization",
                    workload="Microsoft.DirectoryServices",
                    scope="Organization.Read.All",
                ),
            ]
        ),
    )
    world = prof.build_world()
    valid_uris = {
        "https://graph.microsoft.com/beta/devices/",
        "https://graph.microsoft.com/v1.0/organization",
    }
    versions_seen = set()
    for _ in range(200):
        event = generate_graph_api(world)
        assert any(event.RequestUri.startswith(p) for p in valid_uris), event.RequestUri
        if event.RequestUri.endswith("/organization"):
            assert event.ApiVersion == "v1.0"
        elif "/beta/devices/" in event.RequestUri:
            assert event.ApiVersion == "beta"
        versions_seen.add(event.ApiVersion)
    assert versions_seen == {"v1.0", "beta"}


def test_azurehound_profile_loads_and_targets_detection_set():
    """The shipped AzureHound profile generates only the 14 detection URIs."""
    import pathlib
    import re
    import yaml
    from world import Profile

    raw = yaml.safe_load(
        pathlib.Path("examples/threat-profiles/azure-hound/profile.yaml").read_text()
    )
    prof = Profile.model_validate(raw)
    world = prof.build_world()

    uuid_re = re.compile(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )
    azurehound_set = {
        "https://graph.microsoft.com/beta/servicePrincipals/<UUID>/owners",
        "https://graph.microsoft.com/beta/groups/<UUID>/owners",
        "https://graph.microsoft.com/beta/groups/<UUID>/members",
        "https://graph.microsoft.com/v1.0/servicePrincipals/<UUID>/appRoleAssignedTo",
        "https://graph.microsoft.com/beta/applications/<UUID>/owners",
        "https://graph.microsoft.com/beta/devices/<UUID>/registeredOwners",
        "https://graph.microsoft.com/v1.0/users",
        "https://graph.microsoft.com/v1.0/applications",
        "https://graph.microsoft.com/v1.0/groups",
        "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments",
        "https://graph.microsoft.com/v1.0/roleManagement/directory/roleDefinitions",
        "https://graph.microsoft.com/v1.0/devices",
        "https://graph.microsoft.com/v1.0/organization",
        "https://graph.microsoft.com/v1.0/servicePrincipals",
    }
    seen = set()
    for _ in range(600):
        event = generate_graph_api(world)
        normalised = uuid_re.sub("<UUID>", event.RequestUri).split("?")[0]
        seen.add(normalised)
    assert seen <= azurehound_set, seen - azurehound_set
    # The 14 endpoints are uniformly sampled — 600 draws should cover all.
    assert seen == azurehound_set, azurehound_set - seen


def test_graph_api_audit_events_location_override_constrains_region():
    """`graph_api_locations` override fully replaces the default region pool."""
    from world import Overrides, Profile

    prof = Profile(
        tables=["GraphApiAuditEvents"],
        overrides=Overrides(graph_api_locations=["francecentral"]),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_graph_api(world)
        assert event.Location == "francecentral"


def test_graph_api_audit_events_204_has_zero_response_size(_world):
    """204 No Content returns zero body bytes."""
    for _ in range(500):
        event = generate_graph_api(_world)
        if event.ResponseStatusCode == "204":
            assert event.ResponseSize == 0


def test_world_overrides_propagate_into_generated_events():
    """Scalar overrides surface in every generated event."""
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
    """Collection overrides surface in the very next generated event."""
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
    """Bad shapes raise ValidationError, not a downstream KeyError."""
    from pydantic import ValidationError

    from world import Overrides

    with pytest.raises(ValidationError):
        Overrides.model_validate({"users": [{"upn": "missing.fields@northwind.com"}]})


def test_device_process_events_round_trips_through_model(_world):
    event = generate_device_process(_world)

    assert isinstance(event, DeviceProcessEvents)
    DeviceProcessEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_process_events_uses_a_known_device(_world):
    device_ids = {d.device_id for d in _world.devices}
    device_names = {d.device_name for d in _world.devices}
    for _ in range(50):
        event = generate_device_process(_world)
        assert event.DeviceId in device_ids
        assert event.DeviceName in device_names
        assert event.TenantId == TENANT_ID
        assert event.ActionType == "ProcessCreated"


def test_device_logon_events_round_trips_through_model(_world):
    event = generate_device_logon(_world)

    assert isinstance(event, DeviceLogonEvents)
    DeviceLogonEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_logon_events_failure_reason_only_set_on_failure(_world):
    saw_failure = False
    for _ in range(500):
        event = generate_device_logon(_world)
        if event.ActionType == "LogonFailed":
            saw_failure = True
            assert event.FailureReason is not None
        else:
            assert event.ActionType == "LogonSuccess"
            assert event.FailureReason is None
    assert saw_failure, "expected at least one LogonFailed in 500 samples"


def test_device_logon_events_honors_profile_overrides():
    """`device_logon_types`, `device_logon_protocols`, `device_logon_failure_reasons`
    overrides constrain LogonType, Protocol, and FailureReason."""
    from world import DeviceLogonType, Overrides, Profile

    prof = Profile(
        tables=["DeviceLogonEvents"],
        overrides=Overrides(
            device_logon_types=[
                DeviceLogonType(logon_type="Service", weight=1),
                DeviceLogonType(logon_type="Batch", weight=1),
            ],
            device_logon_protocols=["Kerberos"],
            device_logon_failure_reasons=["NorthwindCustomDenial"],
        ),
    )
    world = prof.build_world()

    seen_logon = set()
    saw_failure = False
    for _ in range(500):
        event = generate_device_logon(world)
        assert event.LogonType in {"Service", "Batch"}
        assert event.Protocol == "Kerberos"
        seen_logon.add(event.LogonType)
        if event.ActionType == "LogonFailed":
            saw_failure = True
            assert event.FailureReason == "NorthwindCustomDenial"
    assert seen_logon == {"Service", "Batch"}
    assert saw_failure, "expected at least one LogonFailed in 500 samples"


def test_device_network_events_round_trips_through_model(_world):
    event = generate_device_network(_world)

    assert isinstance(event, DeviceNetworkEvents)
    DeviceNetworkEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_network_events_dns_uses_udp(_world):
    """Port 53 implies Udp."""
    for _ in range(200):
        event = generate_device_network(_world)
        if event.RemotePort == 53:
            assert event.Protocol == "Udp"


def test_device_network_events_honors_network_destinations_override():
    """Custom (port, url) is picked exclusively when network_destinations is overridden."""
    world = World(
        network_destinations=(NetworkDestination(port=8000, url="sfrclak.com"),)
    )
    for _ in range(50):
        event = generate_device_network(world)
        assert event.RemotePort == 8000
        assert event.RemoteUrl == "sfrclak.com"


def test_device_image_load_events_round_trips_through_model(_world):
    event = generate_device_image_load(_world)

    assert isinstance(event, DeviceImageLoadEvents)
    DeviceImageLoadEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_image_load_events_honors_loaded_libraries_override():
    """`loaded_libraries` override fully replaces the default DLL pool."""
    from world import LoadedLibrary, Overrides, Profile

    prof = Profile(
        tables=["DeviceImageLoadEvents"],
        overrides=Overrides(
            loaded_libraries=[
                LoadedLibrary(
                    file_name="northwind-agent.dll",
                    folder_path=r"C:\Program Files\Northwind\bin",
                )
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_device_image_load(world)
        assert event.FileName == "northwind-agent.dll"
        assert event.FolderPath == (
            r"C:\Program Files\Northwind\bin\northwind-agent.dll"
        )


def test_device_registry_events_round_trips_through_model(_world):
    event = generate_device_registry(_world)

    assert isinstance(event, DeviceRegistryEvents)
    DeviceRegistryEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_process_events_honors_pinned_process_sha256():
    """Pinned sha256 on a Process must surface as DeviceProcessEvents.SHA256."""
    from world import Process

    pinned = "ed8560c1ac7ceb6983ba995124d5917dc1a00288912387a6389296637d5f815c"
    world = World(
        processes=(
            Process(
                file_name="powershell.exe",
                folder_path=r"C:\Windows\System32\WindowsPowerShell\v1.0",
                company="Microsoft Corporation",
                description="Windows PowerShell",
                internal_file_name="POWERSHELL",
                original_file_name="PowerShell.EXE.MUI",
                product_name="Microsoft® Windows® Operating System",
                product_version="10.0.19041.3636",
                command_lines=(
                    r"powershell.exe -w hidden -ep bypass -File %TEMP%\6202033.ps1",
                ),
                sha256=pinned,
            ),
        )
    )
    for _ in range(50):
        event = generate_device_process(world)
        assert event.SHA256 == pinned
        assert event.InitiatingProcessSHA256 == pinned


def test_device_registry_events_honors_registry_targets_override():
    """Custom (key, value_name, value_data, value_type) is picked exclusively."""
    world = World(
        registry_targets=(
            RegistryTarget(
                key=r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                value_name="MicrosoftUpdate",
                value_data=r"powershell.exe -w hidden -ep bypass -File %TEMP%\6202033.ps1",
                value_type="REG_SZ",
            ),
        )
    )
    for _ in range(50):
        event = generate_device_registry(world)
        assert (
            event.RegistryKey
            == r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
        )
        assert event.RegistryValueName == "MicrosoftUpdate"
        assert (
            event.RegistryValueData
            == r"powershell.exe -w hidden -ep bypass -File %TEMP%\6202033.ps1"
        )
        assert event.RegistryValueType == "REG_SZ"


def test_device_events_round_trips_through_model(_world):
    event = generate_device_events(_world)

    assert isinstance(event, DeviceEvents)
    DeviceEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_events_honors_action_pool_override():
    """`device_event_actions` override constrains ActionType + drives shape:
    a `file`-shape action populates file fields, `network`-shape doesn't."""
    from world import DeviceEventAction, Overrides, Profile

    prof = Profile(
        tables=["DeviceEvents"],
        overrides=Overrides(
            device_event_actions=[
                DeviceEventAction(
                    action="NorthwindCustomFileDetection",
                    shape="file",
                    weight=1,
                ),
                DeviceEventAction(
                    action="NorthwindCustomNetworkBlock",
                    shape="network",
                    weight=1,
                ),
            ]
        ),
    )
    world = prof.build_world()

    seen = set()
    for _ in range(200):
        event = generate_device_events(world)
        seen.add(event.ActionType)
        assert event.ActionType in {
            "NorthwindCustomFileDetection",
            "NorthwindCustomNetworkBlock",
        }
        if event.ActionType == "NorthwindCustomFileDetection":
            assert event.FileName is not None
            assert event.RemoteIP is None
        else:
            assert event.RemoteIP is not None
            assert event.FileName is None
    assert seen == {"NorthwindCustomFileDetection", "NorthwindCustomNetworkBlock"}


def test_device_file_events_round_trips_through_model(_world):
    event = generate_device_file(_world)

    assert isinstance(event, DeviceFileEvents)
    DeviceFileEvents.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_file_events_share_actions_populate_request_block(_world):
    """NetworkShare* actions populate Request* + ShareName; local actions don't."""
    saw_share = saw_local = False
    for _ in range(500):
        event = generate_device_file(_world)
        if event.ActionType.startswith("NetworkShare"):
            saw_share = True
            assert event.ShareName is not None
            assert event.RequestProtocol == "SMB"
            assert event.RequestSourceIP is not None
            assert event.RequestSourcePort is not None
            assert event.FolderPath.startswith("\\\\")
        else:
            saw_local = True
            assert event.RequestProtocol is None
            assert event.RequestSourceIP is None
    assert saw_share, "expected at least one NetworkShare* action in 500 samples"
    assert saw_local, "expected at least one local file action in 500 samples"


def test_device_file_events_rename_populates_previous_fields(_world):
    """FileRenamed is the only action that fills PreviousFileName / PreviousFolderPath."""
    saw_rename = False
    for _ in range(500):
        event = generate_device_file(_world)
        if event.ActionType == "FileRenamed":
            saw_rename = True
            assert event.PreviousFileName is not None
            assert event.PreviousFolderPath is not None
            assert event.PreviousFolderPath.endswith(event.PreviousFileName)
        else:
            assert event.PreviousFileName is None
            assert event.PreviousFolderPath is None
    assert saw_rename, "expected at least one FileRenamed in 500 samples"


def test_device_file_events_honors_profile_overrides():
    """Profile overrides for templates/actions/labels/hosts flow into rows."""
    from world import (
        FileActionType,
        FileTemplate,
        Overrides,
        Profile,
        SensitivityLabel,
    )

    prof = Profile(
        tables=["DeviceFileEvents"],
        overrides=Overrides(
            file_templates=[
                FileTemplate(
                    folder_template=r"C:\Lab\{user}",
                    file_name="lab-only.docx",
                    kind="doc",
                ),
                FileTemplate(
                    folder_template=r"\\labshare\Drop",
                    file_name="payload.bin",
                    kind="share",
                ),
            ],
            file_action_types=[
                FileActionType(action="FileCreated", weight=1),
                FileActionType(action="NetworkShareFileSynchronized", weight=1),
            ],
            file_sensitivity_labels=[SensitivityLabel(label="Lab-Only")],
            file_download_hosts=["lab.northwind.test"],
        ),
    )
    world = prof.build_world()

    seen_files = set()
    seen_actions = set()
    for _ in range(200):
        event = generate_device_file(world)
        seen_files.add(event.FileName)
        seen_actions.add(event.ActionType)
        assert event.FileName in {"lab-only.docx", "payload.bin"}
        assert event.ActionType in {"FileCreated", "NetworkShareFileSynchronized"}
        if event.SensitivityLabel is not None:
            assert event.SensitivityLabel == "Lab-Only"
    assert seen_files == {"lab-only.docx", "payload.bin"}
    assert seen_actions == {"FileCreated", "NetworkShareFileSynchronized"}


def test_device_file_events_download_origin_only_on_file_created(_world):
    """FileOrigin* is only set for browser-downloaded files freshly created."""
    saw_origin = False
    for _ in range(500):
        event = generate_device_file(_world)
        if event.FileOriginUrl is not None:
            saw_origin = True
            assert event.ActionType == "FileCreated"
            assert event.FileOriginIP is not None
            assert event.FileOriginReferrerUrl is not None
            assert "Downloads" in event.FolderPath
    assert saw_origin, "expected at least one download-origin row in 500 samples"


def test_device_file_certificate_info_round_trips_through_model(_world):
    event = generate_device_cert(_world)

    assert isinstance(event, DeviceFileCertificateInfo)
    DeviceFileCertificateInfo.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_file_certificate_info_unsigned_files_have_no_cert_fields(_world):
    """IsSigned=False clears the cert-specific fields."""
    saw_unsigned = False
    for _ in range(500):
        event = generate_device_cert(_world)
        if event.IsSigned is False:
            saw_unsigned = True
            assert event.Issuer is None
            assert event.Signer is None
            assert event.CertificateSerialNumber is None
    assert saw_unsigned, "expected at least one unsigned row in 500 samples"


def test_device_file_certificate_info_honors_profile_overrides():
    """`code_signing_certificates`, `signed_files`, `crl_urls` overrides flow
    into emitted rows; SHA1 is derived from the picked signed_files entry."""
    from world import CodeSigningCertificate, Overrides, Profile
    from generators.device_common import hashes_for as _hashes_for

    prof = Profile(
        tables=["DeviceFileCertificateInfo"],
        overrides=Overrides(
            code_signing_certificates=[
                CodeSigningCertificate(
                    subject="Northwind Lab CA",
                    issuer="Northwind Lab Root",
                    serial="DEADBEEF00112233",
                    is_root_microsoft=False,
                    signature_type="Catalog",
                )
            ],
            signed_files=["lab-runner.exe"],
            crl_urls=["http://crl.lab.northwind.test/root.crl"],
        ),
    )
    world = prof.build_world()
    expected_sha1 = _hashes_for("lab-runner.exe")[1]

    saw_signed = False
    for _ in range(200):
        event = generate_device_cert(world)
        assert event.SHA1 == expected_sha1
        if event.IsSigned:
            saw_signed = True
            assert event.Signer == "Northwind Lab CA"
            assert event.Issuer == "Northwind Lab Root"
            assert event.CertificateSerialNumber == "DEADBEEF00112233"
            assert event.SignatureType == "Catalog"
            assert event.IsRootSignerMicrosoft is False
            assert event.CrlDistributionPointUrls == (
                "http://crl.lab.northwind.test/root.crl"
            )
    assert saw_signed, "expected at least one signed row in 200 samples"


def test_device_network_info_round_trips_through_model(_world):
    event = generate_device_network_info(_world)

    assert isinstance(event, DeviceNetworkInfo)
    DeviceNetworkInfo.model_validate_json(event.model_dump_json(by_alias=True))


def test_device_network_info_ip_addresses_is_valid_json(_world):
    """IPAddresses is a JSON array round-trippable to a list of dicts."""
    import json

    for _ in range(50):
        event = generate_device_network_info(_world)
        parsed = json.loads(event.IPAddresses)
        assert isinstance(parsed, list)
        assert all("IPAddress" in entry for entry in parsed)


def test_device_event_uses_primary_user_for_its_device(_world):
    """primary_user_upn biases InitiatingProcess selection on its device."""
    primary_upns = {d.primary_user_upn for d in _world.devices if d.primary_user_upn}
    saw_match = False
    for _ in range(500):
        event = generate_device_process(_world)
        device_match = next(
            (d for d in _world.devices if d.device_id == event.DeviceId), None
        )
        if (
            device_match
            and device_match.primary_user_upn
            and event.InitiatingProcessAccountUpn == device_match.primary_user_upn
        ):
            saw_match = True
    assert saw_match, (
        "expected primary_user_upn to be picked for its own device in 500 samples"
    )
    assert primary_upns


def test_processes_override_constrains_initiating_process():
    """A `processes:` override fully replaces the default catalogue."""
    from world import Overrides, Process, Profile

    only_proc = Process(
        file_name="lab-runner.exe",
        folder_path=r"C:\LAB",
        company="Northwind Lab",
        description="Lab Runner",
        internal_file_name="lab-runner",
        original_file_name="LAB-RUNNER.EXE",
        product_name="Northwind Lab Tools",
        product_version="1.2.3",
        command_lines=("lab-runner.exe --once",),
        integrity_level="High",
        elevation="Full",
        signature_status="Valid",
        signer_type="ThirdParty",
        parent="services.exe",
    )
    prof = Profile(
        tables=["DeviceLogonEvents"],
        overrides=Overrides(processes=[only_proc]),
    )
    world = prof.build_world()

    assert len(world.processes) == 1
    for _ in range(50):
        event = generate_device_logon(world)
        assert event.InitiatingProcessFileName == "lab-runner.exe"
        assert event.InitiatingProcessCommandLine == "lab-runner.exe --once"
        assert event.InitiatingProcessVersionInfoCompanyName == "Northwind Lab"
        assert event.InitiatingProcessIntegrityLevel == "High"


def test_devices_override_replaces_world_devices():
    """A `devices:` override fully replaces the default pool."""
    from world import Device, Overrides, Profile

    only_device = Device(
        device_id="ffffffff-aaaa-bbbb-cccc-111111111111",
        device_name="WIN-LAB-ONLY.northwind.local",
        os_platform="Windows11",
        local_ip="10.99.0.5",
        machine_group="Lab",
        primary_user_upn=None,
    )
    prof = Profile(
        tables=["DeviceProcessEvents"],
        overrides=Overrides(devices=[only_device]),
    )
    world = prof.build_world()

    assert len(world.devices) == 1
    for _ in range(50):
        event = generate_device_process(world)
        assert event.DeviceId == only_device.device_id
        assert event.DeviceName == only_device.device_name
        assert event.MachineGroup == "Lab"


@pytest.mark.parametrize("table", sorted(GENERATORS))
def test_every_registered_generator_produces_a_valid_event(table, _world):
    event = GENERATORS[table](_world)
    payload = event.model_dump_json(by_alias=True)
    type(event).model_validate_json(payload)


def test_cloud_app_events_honors_profile_overrides():
    """`cloud_apps`, `cloud_app_file_names`, `cloud_app_mail_subjects`,
    `cloud_app_group_names` overrides flow into emitted rows."""
    from world import CloudApp, Overrides, Profile

    prof = Profile(
        tables=["CloudAppEvents"],
        overrides=Overrides(
            cloud_apps=[
                CloudApp(
                    name="NorthwindLOB",
                    app_id=99999,
                    instance_id=8888,
                    audit_source="Northwind",
                    actions=("FileDownloaded", "MailSent"),
                )
            ],
            cloud_app_file_names=["only-file.csv"],
            cloud_app_mail_subjects=["only-subject"],
        ),
    )
    world = prof.build_world()
    seen_actions = set()
    for _ in range(100):
        event = generate_cae(world)
        assert event.Application == "NorthwindLOB"
        assert event.ApplicationId == 99999
        assert event.AppInstanceId == 8888
        assert event.AuditSource == "Northwind"
        assert event.ActionType in {"FileDownloaded", "MailSent"}
        seen_actions.add(event.ActionType)
        if event.ObjectType == "File":
            assert event.ObjectName == "only-file.csv"
        if event.ObjectType == "Email":
            assert event.ObjectName == "only-subject"
    assert seen_actions == {"FileDownloaded", "MailSent"}


def test_device_network_events_honors_action_types_override():
    """`device_network_action_types` override constrains ActionType."""
    from world import DeviceNetworkActionType, Overrides, Profile

    prof = Profile(
        tables=["DeviceNetworkEvents"],
        overrides=Overrides(
            device_network_action_types=[
                DeviceNetworkActionType(action="NorthwindBeacon", weight=1)
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_device_network(world)
        assert event.ActionType == "NorthwindBeacon"


def test_device_network_info_honors_overrides():
    """`network_adapters`, `local_dns_servers`, `local_default_gateways` flow through."""
    import json

    from world import NetworkAdapter, Overrides, Profile

    prof = Profile(
        tables=["DeviceNetworkInfo"],
        overrides=Overrides(
            network_adapters=[
                NetworkAdapter(
                    name="northwind-vpn0",
                    type="Tunnel",
                    vendor="Northwind Labs",
                    tunnel="Wireguard",
                    network_category="Private",
                    network_name="nw-corp",
                )
            ],
            local_dns_servers=["10.99.0.1", "10.99.0.2"],
            local_default_gateways=["10.99.0.254"],
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_device_network_info(world)
        assert event.NetworkAdapterName == "northwind-vpn0"
        assert event.NetworkAdapterVendor == "Northwind Labs"
        assert event.TunnelType == "Wireguard"
        assert event.IPv4Dhcp == "10.99.0.254"
        assert json.loads(event.DefaultGateways) == ["10.99.0.254"]
        for dns in json.loads(event.DnsAddresses):
            assert dns in {"10.99.0.1", "10.99.0.2"}


def test_device_registry_events_honors_action_types_override():
    """`device_registry_action_types` override constrains ActionType."""
    from world import DeviceRegistryActionType, Overrides, Profile

    prof = Profile(
        tables=["DeviceRegistryEvents"],
        overrides=Overrides(
            device_registry_action_types=[
                DeviceRegistryActionType(action="RegistryValueSet", weight=1)
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_device_registry(world)
        assert event.ActionType == "RegistryValueSet"


def test_email_post_delivery_paths_override():
    """`email_post_delivery_paths` constrains Action / Trigger / DeliveryLocation
    on non-phish mail. (Phish-mail filtering still requires ZAP/Admin paths,
    so the test pins a ZAP path so phish rows can still pick it.)"""
    from world import EmailPostDeliveryPath, Overrides, Profile

    prof = Profile(
        tables=["EmailPostDeliveryEvents"],
        overrides=Overrides(
            email_post_delivery_paths=[
                EmailPostDeliveryPath(
                    action="Northwind ZAP",
                    action_type="Phish ZAP",
                    trigger="ZAP",
                    result="Success",
                    delivery_location="Quarantine",
                )
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_email_post_delivery(world)
        assert event.Action == "Northwind ZAP"
        assert event.ActionTrigger == "ZAP"
        assert event.DeliveryLocation == "Quarantine"


def test_graph_api_status_codes_override_constrains_distribution():
    """`graph_api_status_codes` override constrains ResponseStatusCode."""
    from world import GraphApiStatusCode, Overrides, Profile

    prof = Profile(
        tables=["GraphApiAuditEvents"],
        overrides=Overrides(
            graph_api_status_codes=[GraphApiStatusCode(code="418", weight=1)]
        ),
    )
    world = prof.build_world()
    for _ in range(100):
        event = generate_graph_api(world)
        assert event.ResponseStatusCode == "418"


def test_identity_account_info_honors_auth_method_and_risk_overrides():
    """`identity_auth_methods` and `identity_risk_levels` constrain the row."""
    from world import IdentityRiskLevel, Overrides, Profile

    prof = Profile(
        tables=["IdentityAccountInfo"],
        overrides=Overrides(
            identity_auth_methods=["NorthwindFedAuth"],
            identity_risk_levels=[IdentityRiskLevel(level=3, weight=1)],
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_account_info(world)
        assert event.AuthenticationMethod == "NorthwindFedAuth"
        assert event.DefenderRiskLevel == 3


def test_identity_directory_action_types_override():
    """`identity_directory_action_types` override constrains ActionType."""
    from world import IdentityDirectoryActionType, Overrides, Profile

    prof = Profile(
        tables=["IdentityDirectoryEvents"],
        overrides=Overrides(
            identity_directory_action_types=[
                IdentityDirectoryActionType(
                    action="Northwind custom directory event", weight=1
                )
            ]
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_directory(world)
        assert event.ActionType == "Northwind custom directory event"


def test_identity_events_raw_actions_override():
    """`identity_raw_actions` constrains ActionType + Application + target shape."""
    from world import IdentityRawAction, Overrides, Profile

    prof = Profile(
        tables=["IdentityEvents"],
        overrides=Overrides(
            identity_raw_actions=[
                IdentityRawAction(
                    action="northwind.user.login",
                    application="NorthwindIDP",
                    target_kind="user",
                    weight=1,
                )
            ],
            identity_event_group_names=["NorthwindOnly"],
            identity_event_app_names=["NorthwindLOB"],
        ),
    )
    world = prof.build_world()
    for _ in range(50):
        event = generate_identity(world)
        assert event.ActionType == "northwind.user.login"
        assert event.Application == "NorthwindIDP"


def test_identity_logon_events_overrides():
    """LogonType / Protocol / FailureReason all flow from world."""
    from world import (
        IdentityLogonProtocol,
        IdentityLogonType,
        Overrides,
        Profile,
    )

    prof = Profile(
        tables=["IdentityLogonEvents"],
        overrides=Overrides(
            identity_logon_types=[
                IdentityLogonType(logon_type="Interactive", weight=1)
            ],
            identity_logon_protocols=[
                IdentityLogonProtocol(protocol="NorthwindAuth", port=4444, weight=1)
            ],
            identity_logon_failure_reasons=["NorthwindCustomDenial"],
        ),
    )
    world = prof.build_world()
    saw_failure = False
    for _ in range(500):
        event = generate_logon(world)
        assert event.LogonType == "Interactive"
        assert event.Protocol == "NorthwindAuth"
        assert event.DestinationPort == "4444"
        if event.ActionType == "LogonFailed":
            saw_failure = True
            assert event.FailureReason == "NorthwindCustomDenial"
    assert saw_failure, "expected at least one LogonFailed in 500 samples"


def test_identity_query_events_overrides():
    """`identity_query_kinds` constrains QueryType + Protocol + DestinationPort,
    and the group/computer target pools surface in QueryTarget."""
    from world import IdentityQueryKind, Overrides, Profile

    prof = Profile(
        tables=["IdentityQueryEvents"],
        overrides=Overrides(
            identity_query_kinds=[
                IdentityQueryKind(
                    query_type="QueryGroup", protocol="Ldap", port=389, weight=1
                ),
                IdentityQueryKind(
                    query_type="QueryComputer", protocol="Ldap", port=389, weight=1
                ),
            ],
            identity_query_group_targets=["northwind-only-group"],
            identity_query_computer_targets=["NW-FS-01"],
        ),
    )
    world = prof.build_world()
    seen_targets = set()
    for _ in range(200):
        event = generate_query(world)
        assert event.QueryType in {"QueryGroup", "QueryComputer"}
        seen_targets.add(event.QueryTarget)
    assert seen_targets <= {"northwind-only-group", "NW-FS-01"}
    assert "northwind-only-group" in seen_targets
    assert "NW-FS-01" in seen_targets


def test_url_click_outcomes_override():
    """`url_click_outcomes` and `url_click_workloads` flow into rows."""
    from world import Overrides, Profile, UrlClickOutcome, Workload

    prof = Profile(
        tables=["UrlClickEvents"],
        overrides=Overrides(
            url_click_outcomes=[
                UrlClickOutcome(
                    action_type="NorthwindAllow",
                    is_clicked_through=True,
                    weight=1,
                )
            ],
            url_click_workloads=[Workload(workload="Email", weight=1)],
        ),
    )
    world = prof.build_world()
    # Many runs — but some rows will be phish (forced block path), which falls
    # back to the only available outcome; that's fine.
    for _ in range(100):
        event = generate_url_click(world)
        assert event.ActionType == "NorthwindAllow"
        assert event.Workload == "Email"
