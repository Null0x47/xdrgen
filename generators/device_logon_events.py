from __future__ import annotations

import random

from generators.base import register
from generators.device_common import (
    envelope,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
    sid_for,
)
from models import DeviceLogonEvents
from world import World

# Defender for Endpoint LogonType vocabulary. Weights bias toward the
# everyday cases on managed endpoints (Network for share access,
# Interactive for desktop sign-in). The set matches what `DeviceLogonEvents`
# actually emits, which is a slightly different shape from MDI's
# `IdentityLogonEvents`.
_LOGON_TYPES = [
    ("Network", 50),
    ("Interactive", 18),
    ("RemoteInteractive", 10),
    ("Service", 8),
    ("Batch", 4),
    ("Unlock", 4),
    ("NetworkCleartext", 2),
    ("CachedInteractive", 4),
]
_LOGON_TYPE_VALUES, _LOGON_TYPE_WEIGHTS = zip(*_LOGON_TYPES)

# Authentication protocol — pair with the destination port the client
# actually used. Kerberos / NTLM dominate; NetLogon shows up when the
# logon was forwarded to a DC.
_PROTOCOLS = ("Kerberos", "Ntlm", "NetLogon")

_FAILURE_REASONS = (
    "InvalidUserNameOrPassword",
    "AccountDisabled",
    "AccountExpired",
    "AccountLockedOut",
    "PasswordExpired",
    "UnknownUser",
    "TimeSkew",
    "SmartcardRequired",
)


@register("DeviceLogonEvents")
def generate(world: World) -> DeviceLogonEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)
    ip = random.choice(world.ips)

    success = random.random() < 0.92
    action_type = "LogonSuccess" if success else "LogonFailed"
    logon_type = random.choices(_LOGON_TYPE_VALUES, weights=_LOGON_TYPE_WEIGHTS, k=1)[0]
    protocol = random.choice(_PROTOCOLS)
    logon_id = random.randint(100_000, 9_999_999)

    # Network-style logons typically come from a remote machine. Interactive
    # / cached-interactive ones are local and leave RemoteIP/Port null.
    is_remote = logon_type in ("Network", "RemoteInteractive", "NetworkCleartext")
    remote_ip = ip.ip if is_remote else None
    remote_port = random.randint(49152, 65535) if is_remote else None
    remote_ip_type = (
        "Public"
        if is_remote and ip.category in ("Cloud provider", "ISP")
        else ("Private" if is_remote else None)
    )
    remote_device = (
        f"REMOTE-{random.randint(1, 50):02d}.contoso.com" if is_remote else None
    )

    return DeviceLogonEvents(
        AccountDomain=world.on_prem_ad_domain,
        AccountName=user.sam_account_name,
        AccountSid=sid_for(world, user),
        ActionType=action_type,
        AdditionalFields=None,
        AppGuardContainerId=None,
        FailureReason=random.choice(_FAILURE_REASONS) if not success else None,
        IsLocalAdmin=user.type == "Admin",
        LogonId=logon_id,
        LogonType=logon_type,
        Protocol=protocol,
        RemoteDeviceName=remote_device,
        RemoteIP=remote_ip,
        RemoteIPType=remote_ip_type,
        RemotePort=remote_port,
        ReportId=random.randint(10**9, 10**10 - 1),
        Type="DeviceLogonEvents",
        **initiating_process_fields(world, user, integrity_and_elevation=True),
        **envelope(world, device),
    )
