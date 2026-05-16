from __future__ import annotations

import random
import uuid
from datetime import timedelta

from generators.base import register
from generators.common import now_utc
from generators.device_common import (
    envelope,
    hashes_for_process,
    initiating_process_fields,
    pick_device,
    pick_process,
    pick_user_for_device,
    sid_for,
)
from models import DeviceProcessEvents
from world import World

# MDE only emits ProcessCreated today.
_ACTION_TYPES = ["ProcessCreated"]


@register("DeviceProcessEvents")
def generate(world: World) -> DeviceProcessEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    initiator_logon_id = random.randint(100_000, 9_999_999)
    initiator_fields = initiating_process_fields(
        world,
        user,
        integrity_and_elevation=True,
        logon_id=initiator_logon_id,
        signature_fields=True,
    )

    proc = pick_process(world)
    md5, sha1, sha256 = hashes_for_process(proc)
    pid = random.randint(500, 30000)
    creation_time = now_utc() - timedelta(seconds=random.randint(0, 30))

    return DeviceProcessEvents(
        AccountDomain=world.on_prem_ad_domain,
        AccountName=user.sam_account_name,
        AccountObjectId=user.object_id,
        AccountSid=sid_for(world, user),
        AccountUpn=user.upn,
        ActionType=random.choice(_ACTION_TYPES),
        AdditionalFields=None,
        AppGuardContainerId=None,
        CreatedProcessSessionId=random.randint(1, 5),
        FileName=proc.file_name,
        FileSize=random.randint(50_000, 5_000_000),
        FolderPath=f"{proc.folder_path}\\{proc.file_name}",
        IsProcessRemoteSession=False,
        LogonId=initiator_logon_id,
        MD5=md5,
        ProcessCommandLine=random.choice(proc.command_lines),
        ProcessCreationTime=creation_time,
        ProcessId=pid,
        ProcessIntegrityLevel=proc.integrity_level,
        ProcessRemoteSessionDeviceName=None,
        ProcessRemoteSessionIP=None,
        ProcessTokenElevation=proc.elevation,
        ProcessUniqueId=str(uuid.uuid4()),
        ProcessVersionInfoCompanyName=proc.company,
        ProcessVersionInfoFileDescription=proc.description,
        ProcessVersionInfoInternalFileName=proc.internal_file_name,
        ProcessVersionInfoOriginalFileName=proc.original_file_name,
        ProcessVersionInfoProductName=proc.product_name,
        ProcessVersionInfoProductVersion=proc.product_version,
        ReportId=random.randint(10**9, 10**10 - 1),
        SHA1=sha1,
        SHA256=sha256,
        Type="DeviceProcessEvents",
        **initiator_fields,
        **envelope(world, device),
    )
