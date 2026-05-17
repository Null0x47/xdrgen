from __future__ import annotations

import random
from typing import Optional

from generators.base import register
from generators.device_common import (
    envelope,
    hashes_for,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
    sid_for,
)
from models import DeviceFileEvents
from world import World


def _is_unc(folder: str) -> bool:
    return folder.startswith("\\\\")


def _share_name(folder: str) -> Optional[str]:
    # \\host\share\sub\dir → "host\share"
    if not _is_unc(folder):
        return None
    parts = folder.lstrip("\\").split("\\")
    if len(parts) < 2:
        return None
    return f"{parts[0]}\\{parts[1]}"


def _previous_name(file_name: str) -> str:
    if "." in file_name:
        stem, ext = file_name.rsplit(".", 1)
        return f"{stem}.old.{ext}"
    return f"{file_name}.old"


@register("DeviceFileEvents")
def generate(world: World) -> DeviceFileEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    actions = world.file_action_types
    action_type = random.choices(
        [a.action for a in actions],
        weights=[a.weight for a in actions],
        k=1,
    )[0]

    # NetworkShare* actions must land on a UNC path.
    is_share_action = action_type.startswith("NetworkShare")
    templates = world.file_templates
    if is_share_action:
        candidates = [t for t in templates if t.kind == "share"]
        if not candidates:
            candidates = list(templates)
    else:
        candidates = list(templates)
    template = random.choice(candidates)
    folder_template, file_name, kind = (
        template.folder_template,
        template.file_name,
        template.kind,
    )

    sam = user.sam_account_name or "user"
    folder_path = folder_template.format(user=sam)
    full_path = f"{folder_path}\\{file_name}"

    md5, sha1, sha256 = hashes_for(file_name)
    file_size = random.randint(1_024, 25_000_000)

    file_origin_ip = file_origin_url = file_origin_referrer = None
    if (
        kind == "download"
        and action_type == "FileCreated"
        and world.file_download_hosts
    ):
        host = random.choice(world.file_download_hosts)
        file_origin_url = f"https://{host}/share/{file_name}"
        file_origin_ip = random.choice(world.ips).ip
        file_origin_referrer = f"https://{host}/"

    previous_file_name = previous_folder_path = None
    if action_type == "FileRenamed":
        previous_file_name = _previous_name(file_name)
        previous_folder_path = f"{folder_path}\\{previous_file_name}"

    share_name = _share_name(folder_path)
    sensitivity_label = sensitivity_sublabel = None
    if share_name and "HR" in folder_path:
        sensitivity_label, sensitivity_sublabel = "Highly Confidential", "HR"
    elif share_name and "Finance" in folder_path:
        sensitivity_label, sensitivity_sublabel = "Highly Confidential", "Finance"
    elif kind == "doc" and world.file_sensitivity_labels and random.random() < 0.15:
        picked = random.choice(world.file_sensitivity_labels)
        sensitivity_label, sensitivity_sublabel = picked.label, picked.sublabel

    is_aip = bool(sensitivity_label and "Confidential" in sensitivity_label)

    request_account_domain = request_account_name = request_account_sid = None
    request_protocol = request_source_ip = request_source_port = None
    if is_share_action:
        request_account_domain = world.on_prem_ad_domain
        request_account_name = user.sam_account_name
        request_account_sid = sid_for(world, user)
        request_protocol = "SMB"
        request_source_ip = device.local_ip or f"10.10.20.{random.randint(2, 254)}"
        request_source_port = random.randint(49152, 65535)

    return DeviceFileEvents(
        ActionType=action_type,
        AdditionalFields=None,
        AppGuardContainerId=None,
        FileName=file_name,
        FileOriginIP=file_origin_ip,
        FileOriginReferrerUrl=file_origin_referrer,
        FileOriginUrl=file_origin_url,
        FileSize=file_size,
        FolderPath=full_path,
        IsAzureInfoProtectionApplied=is_aip,
        MD5=md5,
        PreviousFileName=previous_file_name,
        PreviousFolderPath=previous_folder_path,
        ReportId=random.randint(10**9, 10**10 - 1),
        RequestAccountDomain=request_account_domain,
        RequestAccountName=request_account_name,
        RequestAccountSid=request_account_sid,
        RequestProtocol=request_protocol,
        RequestSourceIP=request_source_ip,
        RequestSourcePort=request_source_port,
        SensitivityLabel=sensitivity_label,
        SensitivitySubLabel=sensitivity_sublabel,
        SHA1=sha1,
        SHA256=sha256,
        ShareName=share_name,
        Type="DeviceFileEvents",
        **initiating_process_fields(world, user, integrity_and_elevation=True),
        **envelope(world, device),
    )
