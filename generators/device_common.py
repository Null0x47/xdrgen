"""Shared envelope + InitiatingProcess helpers for Device* generators."""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import timedelta
from typing import Optional

from generators.common import now_utc
from world import Device, Process, User, World


def _hash_for(seed: str, algo: str, length: int) -> str:
    return hashlib.new(algo, seed.encode("utf-8")).hexdigest()[:length]


def hashes_for(file_name: str) -> tuple[str, str, str]:
    """(md5, sha1, sha256), stable per file_name so cross-table pivots agree."""
    seed = f"xdrgen|{file_name}"
    return (
        _hash_for(seed, "md5", 32),
        _hash_for(seed, "sha1", 40),
        _hash_for(seed, "sha256", 64),
    )


def pick_process(world: World) -> Process:
    return random.choice(world.processes)


def pick_device(world: World) -> Device:
    return random.choice(world.devices)


def pick_user_for_device(world: World, device: Device) -> User:
    """75% bias to the device's primary_user_upn; otherwise any world user."""
    if device.primary_user_upn is not None:
        primary = next(
            (u for u in world.users if u.upn == device.primary_user_upn), None
        )
        if primary is not None and random.random() < 0.75:
            return primary
    return random.choice(world.users)


def sid_for(world: World, user: User) -> Optional[str]:
    if user.sid_rid is None:
        return None
    return f"{world.on_prem_sid_prefix}-{user.sid_rid}"


def initiating_process_fields(
    world: World,
    user: User,
    *,
    integrity_and_elevation: bool = False,
    logon_id: Optional[int] = None,
    signature_fields: bool = False,
) -> dict:
    """Universal InitiatingProcess* columns plus optional per-table extras."""
    proc = pick_process(world)
    md5, sha1, sha256 = hashes_for(proc.file_name)
    pid = random.randint(500, 30000)
    parent_pid = random.randint(500, 30000)
    creation_time = now_utc() - timedelta(seconds=random.randint(60, 60 * 60 * 24))
    parent_creation_time = creation_time - timedelta(
        seconds=random.randint(10, 60 * 60 * 24)
    )
    is_remote = random.random() < 0.05

    fields: dict = {
        "InitiatingProcessAccountDomain": world.on_prem_ad_domain,
        "InitiatingProcessAccountName": user.sam_account_name,
        "InitiatingProcessAccountObjectId": user.object_id,
        "InitiatingProcessAccountSid": sid_for(world, user),
        "InitiatingProcessAccountUpn": user.upn,
        "InitiatingProcessCommandLine": random.choice(proc.command_lines),
        "InitiatingProcessCreationTime": creation_time,
        "InitiatingProcessFileName": proc.file_name,
        "InitiatingProcessFileSize": random.randint(50_000, 5_000_000),
        "InitiatingProcessFolderPath": f"{proc.folder_path}\\{proc.file_name}",
        "InitiatingProcessId": pid,
        "InitiatingProcessMD5": md5,
        "InitiatingProcessParentCreationTime": parent_creation_time,
        "InitiatingProcessParentFileName": proc.parent,
        "InitiatingProcessParentId": parent_pid,
        "InitiatingProcessRemoteSessionDeviceName": None,
        "InitiatingProcessRemoteSessionIP": None,
        "InitiatingProcessSessionId": random.randint(1, 5),
        "InitiatingProcessSHA1": sha1,
        "InitiatingProcessSHA256": sha256,
        "InitiatingProcessUniqueId": str(uuid.uuid4()),
        "InitiatingProcessVersionInfoCompanyName": proc.company,
        "InitiatingProcessVersionInfoFileDescription": proc.description,
        "InitiatingProcessVersionInfoInternalFileName": proc.internal_file_name,
        "InitiatingProcessVersionInfoOriginalFileName": proc.original_file_name,
        "InitiatingProcessVersionInfoProductName": proc.product_name,
        "InitiatingProcessVersionInfoProductVersion": proc.product_version,
        "IsInitiatingProcessRemoteSession": is_remote,
    }
    if integrity_and_elevation:
        fields["InitiatingProcessIntegrityLevel"] = proc.integrity_level
        fields["InitiatingProcessTokenElevation"] = proc.elevation
    if logon_id is not None:
        fields["InitiatingProcessLogonId"] = logon_id
    if signature_fields:
        fields["InitiatingProcessSignatureStatus"] = proc.signature_status
        fields["InitiatingProcessSignerType"] = proc.signer_type
    return fields


def envelope(world: World, device: Device) -> dict:
    """Common Device* columns; generators add Type + table-specific fields."""
    return {
        "DeviceId": device.device_id,
        "DeviceName": device.device_name,
        "MachineGroup": device.machine_group,
        "TenantId": world.tenant_id,
        "SourceSystem": "Linux" if device.os_platform == "Linux" else "OpsManager",
        "TimeGenerated": now_utc(),
    }
