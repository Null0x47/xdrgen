"""Shared infrastructure for the `Device*` table generators.

Defender for Endpoint events all share the same envelope shape: a `DeviceId`
/ `DeviceName` / `MachineGroup` triple plus an `InitiatingProcess*` block
that describes the process that produced the event. The helpers here map a
`World` device → user → process so the eight generators stay consistent —
the same `cmd.exe` always reports the same SHA-1, the same
`primary_user_upn` is biased to show up on its device's events, etc.

The catalogue of processes lives on the `World` (`world.processes`) so the
YAML profile can replace it. The default pool covers the binaries Defender
actually surfaces as initiators (Explorer, cmd, PowerShell, svchost,
Chrome, Edge, Outlook, Word, Defender, rundll32) — see `world.py`.
"""

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
    """(md5, sha1, sha256). Stable per `file_name` across the run so analysts
    pivoting on `MsMpEng.exe` always see the same hashes regardless of which
    Device* table the row came from."""
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
    """Bias the picked user toward the device's `primary_user_upn` so events
    on Avery's laptop usually carry Avery's account context. Fall back to a
    random world user when the bias roll fails or the device has no primary
    user — that models shared / unattended endpoints (file servers, build
    boxes) and the occasional secondary login."""
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
    """Return the universal `InitiatingProcess*` columns + the optional
    extras that some Device* tables carry.

    `integrity_and_elevation` adds `InitiatingProcessIntegrityLevel` and
    `InitiatingProcessTokenElevation` (DeviceProcessEvents,
    DeviceLogonEvents, DeviceNetworkEvents, DeviceImageLoadEvents,
    DeviceRegistryEvents). `logon_id` populates `InitiatingProcessLogonId`
    (only DeviceEvents and DeviceProcessEvents). `signature_fields` adds
    `InitiatingProcessSignatureStatus` / `InitiatingProcessSignerType`
    (only DeviceProcessEvents).
    """
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
    """The DeviceId / DeviceName / MachineGroup / TenantId / SourceSystem /
    TimeGenerated common to every Device* row. Generators add `Type` and the
    table-specific columns themselves."""
    return {
        "DeviceId": device.device_id,
        "DeviceName": device.device_name,
        "MachineGroup": device.machine_group,
        "TenantId": world.tenant_id,
        "SourceSystem": "Linux" if device.os_platform == "Linux" else "OpsManager",
        "TimeGenerated": now_utc(),
    }
