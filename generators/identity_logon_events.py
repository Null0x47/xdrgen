from __future__ import annotations

import random

from models import IdentityLogonEvents
from generators.base import register
from generators.common import now_utc, pick, pick_filtered
from world import World


@register("IdentityLogonEvents")
def generate(world: World) -> IdentityLogonEvents:
    user = pick(world.users)
    ip = pick(world.ips)
    ua = pick(world.user_agents)
    dc = pick(world.domain_controllers)
    timestamp = now_utc()

    success = random.random() < 0.92
    action_type = "LogonSuccess" if success else "LogonFailed"

    logon_type = pick(world.identity_logon_types).logon_type

    # Service / Batch logons go via Kerberos TGT (when available).
    if logon_type in ("Service", "Batch"):
        picked_protocol = pick_filtered(
            world.identity_logon_protocols, lambda p: p.protocol == "Kerberos"
        )
    else:
        picked_protocol = pick(world.identity_logon_protocols)
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
            pick(world.identity_logon_failure_reasons).value if not success else None
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
