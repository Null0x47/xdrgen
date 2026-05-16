from __future__ import annotations

import random

from models import IdentityLogonEvents
from generators.base import register
from generators.common import now_utc
from world import World

# Weighted LogonType — Network/Interactive dominate.
_LOGON_TYPES = [
    ("Network", 50),
    ("Interactive", 18),
    ("RemoteInteractive", 12),
    ("Service", 8),
    ("Batch", 4),
    ("Unlock", 4),
    ("NetworkCleartext", 2),
    ("CachedInteractive", 2),
]
_LOGON_TYPE_VALUES, _LOGON_TYPE_WEIGHTS = zip(*_LOGON_TYPES)

# (protocol, destination_port, weight). Kerberos dominates a healthy AD.
_PROTOCOLS = [
    ("Kerberos", 88, 70),
    ("Ntlm", 445, 22),
    ("Ldap", 389, 4),
    ("LdapSecure", 636, 4),
]

_FAILURE_REASONS = [
    "WrongPassword",
    "AccountDisabled",
    "AccountExpired",
    "AccountLockedOut",
    "PasswordExpired",
    "NoSuchUser",
    "TimeSkew",
    "SmartcardRequired",
]


@register("IdentityLogonEvents")
def generate(world: World) -> IdentityLogonEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    ua = random.choice(world.user_agents)
    dc = random.choice(world.domain_controllers)
    timestamp = now_utc()

    success = random.random() < 0.92
    action_type = "LogonSuccess" if success else "LogonFailed"

    logon_type = random.choices(_LOGON_TYPE_VALUES, weights=_LOGON_TYPE_WEIGHTS, k=1)[0]

    # Service / Batch logons go via Kerberos TGT.
    if logon_type in ("Service", "Batch"):
        protocol_choices = [p for p in _PROTOCOLS if p[0] == "Kerberos"]
    else:
        protocol_choices = _PROTOCOLS
    protocol_values, protocol_ports, protocol_weights = zip(*protocol_choices)
    proto_idx = random.choices(
        range(len(protocol_values)), weights=protocol_weights, k=1
    )[0]
    protocol = protocol_values[proto_idx]
    destination_port = protocol_ports[proto_idx]

    sid = (
        f"{world.on_prem_sid_prefix}-{user.sid_rid}"
        if user.sid_rid is not None
        else None
    )

    return IdentityLogonEvents(
        AccountDisplayName=user.display_name,
        AccountDomain=world.on_prem_ad_domain,
        AccountName=user.sam_account_name,
        AccountObjectId=user.object_id,
        AccountSid=sid,
        AccountUpn=user.upn,
        ActionType=action_type,
        AdditionalFields=None,
        Application="Active Directory",
        DestinationDeviceName=dc.name,
        DestinationIPAddress=dc.ip,
        DestinationPort=str(destination_port),
        DeviceName=user.device_name,
        DeviceType="Server" if logon_type == "Service" else ua.device_type,
        FailureReason=random.choice(_FAILURE_REASONS) if not success else None,
        IPAddress=ip.ip,
        ISP=ip.isp,
        LastSeenForUser={
            "IPAddress": random.randint(0, 30),
            "DeviceName": random.randint(0, 30),
            "DestinationDeviceName": random.randint(0, 30),
        },
        Location=f"{ip.city}, {ip.country}",
        LogonType=logon_type,
        OSPlatform=ua.platform,
        Port=str(random.randint(49152, 65535)),
        Protocol=protocol,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceSystem="Azure",
        TargetAccountDisplayName=user.display_name,
        TargetDeviceName=dc.name,
        TenantId=world.tenant_id,
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="IdentityLogonEvents",
        UncommonForUser=[],
    )
