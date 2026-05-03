from __future__ import annotations

import random

from generators.base import register
from generators.device_common import (
    envelope,
    hashes_for,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
)
from models import DeviceImageLoadEvents
from world import World

# Real DLLs commonly loaded on Windows. Each entry pairs the file name with
# a typical folder, so DeviceImageLoadEvents.FolderPath stays consistent
# with the file name (kernel32.dll lives in System32, never in Temp).
_LIBRARIES = [
    ("kernel32.dll", r"C:\Windows\System32"),
    ("ntdll.dll", r"C:\Windows\System32"),
    ("user32.dll", r"C:\Windows\System32"),
    ("advapi32.dll", r"C:\Windows\System32"),
    ("ws2_32.dll", r"C:\Windows\System32"),
    ("crypt32.dll", r"C:\Windows\System32"),
    ("ole32.dll", r"C:\Windows\System32"),
    ("shell32.dll", r"C:\Windows\System32"),
    ("rpcrt4.dll", r"C:\Windows\System32"),
    ("msvcrt.dll", r"C:\Windows\System32"),
    ("amsi.dll", r"C:\Windows\System32"),
    ("wininet.dll", r"C:\Windows\System32"),
    ("urlmon.dll", r"C:\Windows\System32"),
    (
        "System.Management.Automation.dll",
        r"C:\Windows\assembly\NativeImages_v4.0.30319_64",
    ),
]


@register("DeviceImageLoadEvents")
def generate(world: World) -> DeviceImageLoadEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    file_name, folder_path = random.choice(_LIBRARIES)
    md5, sha1, sha256 = hashes_for(file_name)

    return DeviceImageLoadEvents(
        ActionType="ImageLoaded",
        AppGuardContainerId=None,
        FileName=file_name,
        FileSize=random.randint(40_000, 8_000_000),
        FolderPath=f"{folder_path}\\{file_name}",
        MD5=md5,
        SHA1=sha1,
        SHA256=sha256,
        ReportId=random.randint(10**9, 10**10 - 1),
        Type="DeviceImageLoadEvents",
        **initiating_process_fields(world, user, integrity_and_elevation=True),
        **envelope(world, device),
    )
