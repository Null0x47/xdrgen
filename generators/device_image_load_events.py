from __future__ import annotations

import random

from generators.base import register
from generators.common import pick
from generators.device_common import (
    envelope,
    hashes_for,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
)
from models import DeviceImageLoadEvents
from world import World


@register("DeviceImageLoadEvents")
def generate(world: World) -> DeviceImageLoadEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    library = pick(world.loaded_libraries)
    file_name, folder_path = library.file_name, library.folder_path
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
