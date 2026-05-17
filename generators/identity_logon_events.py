from __future__ import annotations

import random

from models import IdentityLogonEvents
from generators.base import register
from generators.common import now_utc
from world import World


@register("IdentityLogonEvents")
def generate(world: World) -> IdentityLogonEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    ua = random.choice(world.user_agents)
    dc = random.choice(world.domain_controllers)
    timestamp = now_utc()

    success = random.random() < 0.92
    action_type = "LogonSuccess" if success else "LogonFailed"

    logon_type = random.choices(
        [t.logon_type for t in world.identity_logon_types],
        weights=[t.weight for t in world.identity_logon_types],
        k=1,
    )[0]

    # Service / Batch logons go via Kerberos TGT (when available).
    if logon_type in ("Service", "Batch"):
        protocol_choices = [
            p for p in world.identity_logon_protocols if p.protocol == "Kerberos"
        ] or list(world.identity_logon_protocols)
    else:
        protocol_choices = list(world.identity_logon_protocols)
    picked_protocol = random.choices(
        protocol_choices, weights=[p.weight for p in protocol_choices], k=1
    )[0]
    protocol = picked_protocol.protocol
    destination_port = picked_protocol.port

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
        FailureReason=(
            random.choice(world.identity_logon_failure_reasons) if not success else None
        ),
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
