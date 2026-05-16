from __future__ import annotations

import random

from generators.base import register
from generators.device_common import (
    envelope,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
)
from models import DeviceRegistryEvents
from world import World

# Weighted ActionType — RegistryValueSet dominates.
_ACTION_TYPES = [
    ("RegistryValueSet", 60),
    ("RegistryKeyCreated", 12),
    ("RegistryValueDeleted", 10),
    ("RegistryKeyDeleted", 8),
    ("RegistryKeyRenamed", 4),
    ("RegistryValueRenamed", 4),
    ("RegistryKeyAndValueDeleted", 2),
]
_ACTION_VALUES, _ACTION_WEIGHTS = zip(*_ACTION_TYPES)


@register("DeviceRegistryEvents")
def generate(world: World) -> DeviceRegistryEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    action_type = random.choices(_ACTION_VALUES, weights=_ACTION_WEIGHTS, k=1)[0]
    target = random.choice(world.registry_targets)
    key, value_name, value_data, value_type = (
        target.key,
        target.value_name,
        target.value_data,
        target.value_type,
    )

    has_previous = "Renamed" in action_type or "Set" in action_type
    previous_key = key if action_type == "RegistryKeyRenamed" else None
    previous_value_name = (
        f"{value_name}_old"
        if has_previous and action_type == "RegistryValueRenamed"
        else (value_name if has_previous else None)
    )
    previous_value_data = "0" if has_previous and value_type == "REG_DWORD" else None

    return DeviceRegistryEvents(
        ActionType=action_type,
        AppGuardContainerId=None,
        PreviousRegistryKey=previous_key,
        PreviousRegistryValueData=previous_value_data,
        PreviousRegistryValueName=previous_value_name,
        RegistryKey=key,
        RegistryValueData=value_data,
        RegistryValueName=value_name,
        RegistryValueType=value_type,
        ReportId=random.randint(10**9, 10**10 - 1),
        Type="DeviceRegistryEvents",
        **initiating_process_fields(world, user, integrity_and_elevation=True),
        **envelope(world, device),
    )
