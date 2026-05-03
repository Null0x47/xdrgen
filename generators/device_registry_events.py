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

# Defender for Endpoint registry-event vocabulary. ValueSet dominates by far
# (every config flip produces one), with key-create / key-rename rarer.
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

# Realistic registry keys / value names / data tuples — pairs that actually
# co-occur on a Windows endpoint. Defender hunters look for hits on Run,
# IFEO, and policy keys, so the catalogue leans into those areas.
_REGISTRY_TARGETS = [
    (
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "OneDrive",
        r"C:\Users\Avery\AppData\Local\Microsoft\OneDrive\OneDrive.exe /background",
        "REG_SZ",
    ),
    (
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
        "Teams",
        r'"C:\Users\Avery\AppData\Local\Microsoft\Teams\Update.exe" --processStart "Teams.exe"',
        "REG_SZ",
    ),
    (
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\sethc.exe",
        "Debugger",
        r"cmd.exe",
        "REG_SZ",
    ),
    (
        r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WinDefend",
        "Start",
        "2",
        "REG_DWORD",
    ),
    (
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender",
        "DisableAntiSpyware",
        "0",
        "REG_DWORD",
    ),
    (
        r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa",
        "RunAsPPL",
        "1",
        "REG_DWORD",
    ),
    (
        r"HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Word\Security",
        "VBAWarnings",
        "2",
        "REG_DWORD",
    ),
    (
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A4B3C5D6-7890-1234-5678-9ABCDEF01234}",
        "DisplayName",
        "Internal Helper Tool",
        "REG_SZ",
    ),
]


@register("DeviceRegistryEvents")
def generate(world: World) -> DeviceRegistryEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    action_type = random.choices(_ACTION_VALUES, weights=_ACTION_WEIGHTS, k=1)[0]
    key, value_name, value_data, value_type = random.choice(_REGISTRY_TARGETS)

    # Modify / rename actions carry both the new and previous values.
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
