from __future__ import annotations

import random

from models import IdentityDirectoryEvents
from generators.base import register
from generators.common import now_utc
from world import World

# Weighted ActionType — group/password churn dominates.
_ACTION_TYPES = [
    ("Group Membership changed", 32),
    ("Account Password changed", 22),
    ("Account enabled", 8),
    ("Account disabled", 6),
    ("Group created", 4),
    ("Group deleted", 2),
    ("User created", 4),
    ("User deleted", 2),
    ("Account name changed", 3),
    ("Account display name changed", 5),
    ("Domain controller authentication policy changed", 1),
    ("Account Constrained Delegation state changed", 1),
    ("Account Unconstrained Delegation state changed", 1),
    ("Account Sensitive flag changed", 2),
    ("Service Principal Name added to account", 4),
    ("Service Principal Name removed from account", 3),
]
_ACTION_VALUES, _ACTION_WEIGHTS = zip(*_ACTION_TYPES)


@register("IdentityDirectoryEvents")
def generate(world: World) -> IdentityDirectoryEvents:
    actor = random.choice(world.users)
    target = random.choice(world.users)
    ip = random.choice(world.ips)
    dc = random.choice(world.domain_controllers)
    timestamp = now_utc()

    action_type = random.choices(_ACTION_VALUES, weights=_ACTION_WEIGHTS, k=1)[0]

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
        TimeGenerated=timestamp,
        Type="IdentityDirectoryEvents",
    )
