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
    WeightedPool,
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


def test_world_pool_fields_are_weighted_pools():
    """WeightedPool wraps each pool — frozen + hashable, with a uniform default."""
    w = World()
    assert isinstance(w.users, WeightedPool)
    assert isinstance(w.ips, WeightedPool)
    assert isinstance(w.client_apps, WeightedPool)
    assert w.users.random is True
    assert isinstance(w.users.entries, tuple)


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


def test_weighted_pool_random_false_requires_weight_on_every_entry():
    """`random: false` must reject entries missing `weight`."""
    with pytest.raises(ValidationError):
        Profile.model_validate(
            {
                "overrides": {
                    "devices": {
                        "random": False,
                        "entries": [
                            {"device_id": "1", "device_name": "ws01", "weight": 5},
                            {"device_id": "2", "device_name": "ws02"},
                        ],
                    }
                }
            }
        )


def test_weighted_pool_random_false_biases_distribution():
    """`random: false` actually picks weighted — heavy entries dominate."""
    import random as _random

    from generators.common import pick

    prof = Profile.model_validate(
        {
            "overrides": {
                "devices": {
                    "random": False,
                    "entries": [
                        {"device_id": "heavy", "device_name": "ws01", "weight": 99},
                        {"device_id": "light", "device_name": "ws02", "weight": 1},
                    ],
                }
            }
        }
    )
    world = prof.build_world()
    _random.seed(0)
    picks = [pick(world.devices).device_id for _ in range(500)]
    heavy_ratio = picks.count("heavy") / len(picks)
    assert heavy_ratio > 0.9, f"expected heavy dominance, got {heavy_ratio:.2f}"


def test_weighted_pool_random_true_ignores_weight():
    """`random: true` (default) samples uniformly, ignoring any per-entry weight."""
    import random as _random

    from generators.common import pick

    prof = Profile.model_validate(
        {
            "overrides": {
                "devices": [
                    {"device_id": "a", "device_name": "ws01", "weight": 99},
                    {"device_id": "b", "device_name": "ws02", "weight": 1},
                ]
            }
        }
    )
    world = prof.build_world()
    assert world.devices.random is True
    _random.seed(0)
    picks = [pick(world.devices).device_id for _ in range(500)]
    a_ratio = picks.count("a") / len(picks)
    # Uniform — within ±10% of 0.5 (would be ~0.99 if weights were honored).
    assert 0.4 < a_ratio < 0.6, f"expected uniform, got {a_ratio:.2f}"


def test_weighted_pool_plain_list_shorthand_is_uniform():
    """Bare list overrides keep the legacy YAML shape and sample uniformly."""
    prof = Profile.model_validate(
        {
            "overrides": {
                "users": [{"display_name": "X", "upn": "x@x", "object_id": "1"}]
            }
        }
    )
    world = prof.build_world()
    assert world.users.random is True
    assert len(world.users) == 1


def test_scalar_pool_accepts_bare_strings():
    """`cloud_app_file_names: ["a.docx"]` is coerced to `[{value: "a.docx"}]`."""
    prof = Profile.model_validate(
        {"overrides": {"cloud_app_file_names": ["report.docx", "salary.xlsx"]}}
    )
    world = prof.build_world()
    assert world.cloud_app_file_names.random is True
    assert [e.value for e in world.cloud_app_file_names] == [
        "report.docx",
        "salary.xlsx",
    ]


def test_scalar_pool_weighted_form_is_honored():
    """`{random: false, entries: [{value, weight}, ...]}` is validated and used."""
    import random as _random

    from generators.common import pick

    prof = Profile.model_validate(
        {
            "overrides": {
                "cloud_app_file_names": {
                    "random": False,
                    "entries": [
                        {"value": "heavy.docx", "weight": 99},
                        {"value": "light.docx", "weight": 1},
                    ],
                }
            }
        }
    )
    world = prof.build_world()
    assert world.cloud_app_file_names.random is False
    _random.seed(0)
    picks = [pick(world.cloud_app_file_names).value for _ in range(200)]
    assert picks.count("heavy.docx") / len(picks) > 0.9


def test_scalar_pool_weighted_form_requires_weight():
    """Scalar pools enforce `weight` per entry when `random: false`."""
    with pytest.raises(ValidationError):
        Profile.model_validate(
            {
                "overrides": {
                    "cloud_app_file_names": {
                        "random": False,
                        "entries": [{"value": "a.docx"}, {"value": "b.docx"}],
                    }
                }
            }
        )


def test_pick_filtered_respects_random_flag():
    """`pick_filtered` filters first, then dispatches uniform or weighted."""
    import random as _random

    from generators.common import pick_filtered

    prof = Profile.model_validate(
        {
            "overrides": {
                "devices": {
                    "random": False,
                    "entries": [
                        {
                            "device_id": "win-heavy",
                            "device_name": "ws01",
                            "weight": 99,
                            "os_platform": "Windows10",
                        },
                        {
                            "device_id": "win-light",
                            "device_name": "ws02",
                            "weight": 1,
                            "os_platform": "Windows10",
                        },
                        {
                            "device_id": "linux-heavy",
                            "device_name": "lx01",
                            "weight": 50,
                            "os_platform": "Linux",
                        },
                    ],
                }
            }
        }
    )
    world = prof.build_world()
    _random.seed(0)
    picks = [
        pick_filtered(world.devices, lambda d: d.os_platform == "Windows10").device_id
        for _ in range(300)
    ]
    assert "linux-heavy" not in picks
    assert picks.count("win-heavy") / len(picks) > 0.9
