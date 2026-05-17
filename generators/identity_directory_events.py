from __future__ import annotations

import random

from models import IdentityDirectoryEvents
from generators.base import register
from generators.common import now_utc
from world import World


@register("IdentityDirectoryEvents")
def generate(world: World) -> IdentityDirectoryEvents:
    actor = random.choice(world.users)
    target = random.choice(world.users)
    ip = random.choice(world.ips)
    dc = random.choice(world.domain_controllers)
    timestamp = now_utc()

    action_type = random.choices(
        [a.action for a in world.identity_directory_action_types],
        weights=[a.weight for a in world.identity_directory_action_types],
        k=1,
    )[0]

    return IdentityDirectoryEvents(
        AccountDisplayName=actor.display_name,
        AccountDomain=world.on_prem_ad_domain,
        AccountName=actor.sam_account_name,
        AccountObjectId=actor.object_id,
        AccountSid=(
            f"{world.on_prem_sid_prefix}-{actor.sid_rid}"
            if actor.sid_rid is not None
            else None
        ),
        AccountUpn=actor.upn,
        ActionType=action_type,
        AdditionalFields=None,
        Application="Active Directory",
        DestinationDeviceName=dc.name,
        DestinationIPAddress=dc.ip,
        DestinationPort="389",
        DeviceName=actor.device_name,
        IPAddress=ip.ip,
        ISP=ip.isp,
        Location=f"{ip.city}, {ip.country}",
        Port=str(random.randint(49152, 65535)),
        Protocol="Ldap",
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceSystem="Azure",
        TargetAccountDisplayName=target.display_name,
        TargetAccountUpn=target.upn,
        TargetDeviceName=dc.name,
        TenantId=world.tenant_id,
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="IdentityDirectoryEvents",
    )
