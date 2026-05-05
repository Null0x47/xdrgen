from __future__ import annotations

import pytest
from pydantic import ValidationError

from world import (
    DomainController,
    IPEntry,
    Overrides,
    Profile,
    User,
    WeightedErrorCode,
    World,
)


def test_default_world_has_baked_in_fixtures():
    w = World()
    assert w.tenant_id == "a1b2c3d4-5e6f-4071-8293-94a5b6c7d8e9"
    assert w.tenant_domain == "contoso.com"
    assert w.on_prem_ad_domain == "contoso.local"
    assert len(w.users) == 6
    assert len(w.ips) == 6
    assert len(w.user_agents) == 6
    assert len(w.domain_controllers) == 2
    assert len(w.client_apps) == 8
    assert len(w.resources) == 6
    assert len(w.groups) == 6
    assert len(w.conditional_access_policies) == 3
    assert len(w.entra_sign_in_error_codes) >= 10
    assert len(w.entra_spn_sign_in_error_codes) >= 5
    assert w.entra_sign_in_error_codes[0].code == 0
    assert w.entra_spn_sign_in_error_codes[0].code == 0
    success_weight = w.entra_sign_in_error_codes[0].weight
    failure_weight = sum(c.weight for c in w.entra_sign_in_error_codes if c.code != 0)
    assert success_weight > failure_weight


def test_weighted_error_code_overrides_replace_defaults():
    prof = Profile(
        tables=["EntraIdSignInEvents"],
        overrides=Overrides(
            entra_sign_in_error_codes=[
                WeightedErrorCode(code=0, weight=1),
                WeightedErrorCode(
                    code=50126,
                    weight=99,
                    description="InvalidUserNameOrPassword",
                ),
            ]
        ),
    )
    w = prof.build_world()
    assert len(w.entra_sign_in_error_codes) == 2
    assert w.entra_sign_in_error_codes[1].weight == 99
    assert len(w.entra_spn_sign_in_error_codes) >= 5


def test_weighted_error_code_rejects_unknown_keys():
    with pytest.raises(ValidationError):
        WeightedErrorCode.model_validate({"code": 0, "weight": 1, "extra": True})


def test_world_is_frozen():
    w = World()
    with pytest.raises(ValidationError):
        w.tenant_id = "northwind"


def test_world_collections_are_tuples():
    """Tuples make World hashable + immutable."""
    w = World()
    assert isinstance(w.users, tuple)
    assert isinstance(w.ips, tuple)
    assert isinstance(w.client_apps, tuple)


def test_world_is_hashable():
    """Hashable so `@lru_cache(pool_for(world))` works."""
    a = World()
    b = World()
    assert hash(a) == hash(b)
    assert {a, b} == {a}


def test_profile_build_world_with_no_overrides_returns_default():
    prof = Profile(tables=["CloudAppEvents"])
    w = prof.build_world()
    assert w == World()


def test_profile_tables_is_optional():
    """`tables:` is optional — overrides-only profiles validate."""
    prof = Profile()
    assert prof.tables is None
    prof2 = Profile.model_validate({"overrides": {"tenant_domain": "northwind.com"}})
    assert prof2.tables is None
    assert prof2.build_world().tenant_domain == "northwind.com"


def test_profile_build_world_applies_scalar_override():
    prof = Profile(
        tables=["CloudAppEvents"],
        overrides=Overrides(tenant_id="99999999-aaaa-bbbb-cccc-dddddddddddd"),
    )
    w = prof.build_world()
    assert w.tenant_id == "99999999-aaaa-bbbb-cccc-dddddddddddd"
    assert w.tenant_domain == "contoso.com"
    assert len(w.users) == 6


def test_profile_build_world_replaces_collection_when_supplied():
    prof = Profile(
        tables=["CloudAppEvents"],
        overrides=Overrides(
            users=[
                User(
                    display_name="Lonely Admin",
                    upn="lonely.admin@northwind.com",
                    object_id="11111111-2222-3333-4444-555555555555",
                    type="Admin",
                )
            ]
        ),
    )
    w = prof.build_world()
    assert len(w.users) == 1
    assert w.users[0].upn == "lonely.admin@northwind.com"
    assert len(w.ips) == 6


def test_overrides_rejects_unknown_keys():
    with pytest.raises(ValidationError):
        Overrides.model_validate({"not_a_real_key": "x"})


def test_user_rejects_unknown_keys():
    with pytest.raises(ValidationError):
        User.model_validate(
            {
                "display_name": "X",
                "upn": "x@x",
                "object_id": "00000000-0000-0000-0000-000000000000",
                "this_is_not_a_field": True,
            }
        )


def test_user_minimum_required_fields():
    """Only display_name/upn/object_id are required; type defaults to Regular."""
    u = User(
        display_name="Tiny",
        upn="tiny@x",
        object_id="00000000-0000-0000-0000-000000000000",
    )
    assert u.type == "Regular"
    assert u.sam_account_name is None


def test_domain_controller_round_trip_via_overrides():
    prof = Profile(
        tables=["CloudAppEvents"],
        overrides=Overrides(
            domain_controllers=[
                DomainController(
                    name="DC-NW-01.northwind.local",
                    ip="10.10.0.10",
                    device_id="ffffffff-1111-2222-3333-444444444444",
                )
            ]
        ),
    )
    w = prof.build_world()
    assert len(w.domain_controllers) == 1
    assert w.domain_controllers[0].name == "DC-NW-01.northwind.local"


def test_ip_entry_requires_geo_fields():
    with pytest.raises(ValidationError):
        IPEntry(ip="9.9.9.9")
