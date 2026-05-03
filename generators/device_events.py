from __future__ import annotations

import random
from datetime import timedelta

from generators.base import register
from generators.common import now_utc
from generators.device_common import (
    envelope,
    hashes_for,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
    sid_for,
)
from models import DeviceEvents
from world import World

# DeviceEvents is the catch-all MDE table. ActionType pulls from a wide
# vocabulary covering Antivirus, ASR, Network Protection, Tamper Protection,
# WDAC, AMSI, and other mixed-shape events. Each entry declares which
# auxiliary block (file / network / registry) the event populates so the
# row stays internally consistent.
#
# (action_type, shape) where shape ∈ {"file", "network", "registry", "none"}.
_ACTION_TYPES = [
    ("AntivirusDetection", "file"),
    ("AntivirusDetectionAndBlock", "file"),
    ("AntivirusReport", "file"),
    ("ExploitGuardNetworkProtectionBlocked", "network"),
    ("ExploitGuardNetworkProtectionAudited", "network"),
    ("AsrLsassCredentialTheftAudited", "none"),
    ("AsrOfficeChildProcessBlocked", "file"),
    ("AsrUntrustedExecutableAudited", "file"),
    ("BrowserLaunchedToOpenUrl", "network"),
    ("ScreenshotTaken", "none"),
    ("PowerShellCommand", "none"),
    ("AmsiScriptDetection", "none"),
    ("ControlFlowGuardViolation", "none"),
    ("TamperingAttempt", "registry"),
    ("AppControlPolicyApplied", "none"),
    ("OpenProcessApiCall", "none"),
    ("UsbDriveMounted", "none"),
    ("UsbDriveUnmounted", "none"),
    ("UserAccountAddedToLocalGroup", "none"),
]


@register("DeviceEvents")
def generate(world: World) -> DeviceEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)

    action_type, shape = random.choice(_ACTION_TYPES)
    initiator_logon_id = random.randint(100_000, 9_999_999)
    initiator_fields = initiating_process_fields(
        world, user, logon_id=initiator_logon_id
    )

    # Optional file-related fields — populated when the action surfaces a file.
    file_name = file_size = folder_path = md5 = sha1 = sha256 = None
    file_origin_ip = file_origin_url = None
    if shape == "file":
        file_name = random.choice(
            ["malware.exe", "invoice.docx.exe", "loader.dll", "macro.docm"]
        )
        folder_path = (
            rf"C:\Users\{user.sam_account_name or 'user'}\Downloads\{file_name}"
        )
        file_size = random.randint(20_000, 5_000_000)
        md5, sha1, sha256 = hashes_for(file_name)
        file_origin_url = "https://acme-files.example.com/share/" + file_name
        file_origin_ip = random.choice(world.ips).ip

    # Optional process-creation fields — populated when DeviceEvents stands
    # in for a sub-process spawn (e.g. Office child process blocked).
    proc_command_line = proc_creation_time = proc_id = proc_token = None
    is_proc_remote = None
    if action_type in ("AsrOfficeChildProcessBlocked", "AsrUntrustedExecutableAudited"):
        proc_command_line = random.choice(
            [
                r"powershell.exe -EncodedCommand JABz...",
                r"cmd.exe /c whoami /all",
                r"rundll32.exe shell32.dll,Control_RunDLL",
            ]
        )
        proc_creation_time = now_utc() - timedelta(seconds=random.randint(0, 30))
        proc_id = random.randint(500, 30000)
        proc_token = "Default"
        is_proc_remote = False

    # Optional network-related fields — populated for Network Protection /
    # browser-launched URL events.
    local_ip = local_port = remote_ip = remote_port = remote_url = None
    if shape == "network":
        local_ip = device.local_ip or f"10.10.20.{random.randint(2, 254)}"
        local_port = random.randint(49152, 65535)
        remote_ip_entry = random.choice(world.ips)
        remote_ip = remote_ip_entry.ip
        remote_port = 443
        remote_url = random.choice(
            [
                "malicious.example.org",
                "phish-login.example.net",
                "tracker.contoso-bad.example",
            ]
        )

    # Optional registry-related fields — populated for tampering attempts.
    registry_key = registry_value_name = registry_value_data = None
    if shape == "registry":
        registry_key = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
        registry_value_name = "DisableRealtimeMonitoring"
        registry_value_data = "1"

    return DeviceEvents(
        AccountDomain=world.on_prem_ad_domain,
        AccountName=user.sam_account_name,
        AccountSid=sid_for(world, user),
        ActionType=action_type,
        AdditionalFields=None,
        AppGuardContainerId=None,
        CreatedProcessSessionId=random.randint(1, 5) if proc_id else None,
        FileName=file_name,
        FileOriginIP=file_origin_ip,
        FileOriginUrl=file_origin_url,
        FileSize=file_size,
        FolderPath=folder_path,
        IsProcessRemoteSession=is_proc_remote,
        LocalIP=local_ip,
        LocalPort=local_port,
        LogonId=initiator_logon_id,
        MD5=md5,
        ProcessCommandLine=proc_command_line,
        ProcessCreationTime=proc_creation_time,
        ProcessId=proc_id,
        ProcessRemoteSessionDeviceName=None,
        ProcessRemoteSessionIP=None,
        ProcessTokenElevation=proc_token,
        RegistryKey=registry_key,
        RegistryValueData=registry_value_data,
        RegistryValueName=registry_value_name,
        RemoteDeviceName=None,
        RemoteIP=remote_ip,
        RemotePort=remote_port,
        RemoteUrl=remote_url,
        ReportId=random.randint(10**9, 10**10 - 1),
        SHA1=sha1,
        SHA256=sha256,
        Type="DeviceEvents",
        **initiator_fields,
        **envelope(world, device),
    )
