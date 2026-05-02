from __future__ import annotations

import random

from models import IdentityQueryEvents
from generators.base import register
from generators.common import now_utc
from world import World

# (QueryType, Protocol, Port) — Defender for Identity surfaces queries that
# came in over LDAP, SAMR (\\PIPE\\samr over SMB on 445), or Kerberos
# (s4u2self / forwardable lookups). DNS QueryTypes also exist for some
# enumeration patterns.
_QUERY_KINDS = [
    ("QueryUser", "Ldap", 389, 35),
    ("QueryGroup", "Ldap", 389, 25),
    ("EnumerateUsers", "Samr", 445, 12),
    ("EnumerateGroups", "Samr", 445, 8),
    ("QueryComputer", "Ldap", 389, 8),
    ("QueryDomain", "Ldap", 389, 5),
    ("Resolve", "Dns", 53, 7),
]
_QUERY_VALUES, _QUERY_PROTOCOLS, _QUERY_PORTS, _QUERY_WEIGHTS = zip(*_QUERY_KINDS)

# A small bag of group / OU / computer names that show up as QueryTarget
# values in real recon traffic (BloodHound-style enumeration tends to walk
# Domain Admins, Enterprise Admins, and tier-0 OUs).
_GROUP_TARGETS = [
    "Domain Admins",
    "Enterprise Admins",
    "Schema Admins",
    "Backup Operators",
    "Account Operators",
    "Server Operators",
    "Engineering",
    "Finance",
    "All Employees",
]
_COMPUTER_TARGETS = [
    "DC01",
    "DC02",
    "FS01",
    "EXCH01",
    "CRM-DB-PROD",
    "BUILD-AGENT-03",
]


def _query_target_for_kind(query_type: str, world: World) -> str:
    if "Group" in query_type:
        return random.choice(_GROUP_TARGETS)
    if "Computer" in query_type:
        return random.choice(_COMPUTER_TARGETS)
    if query_type == "QueryDomain":
        return world.on_prem_ad_domain
    if query_type == "Resolve":
        return random.choice(_COMPUTER_TARGETS) + f".{world.on_prem_ad_domain}"
    # Default: user / unspecified — pick a sAMAccountName from the user pool.
    candidates = [u for u in world.users if u.sam_account_name]
    pick = random.choice(candidates) if candidates else random.choice(world.users)
    return pick.sam_account_name or pick.upn


def _ldap_query_string(query_type: str, target: str) -> str:
    """Build a plausible LDAP-style filter for the given query."""
    if query_type == "QueryUser":
        return f"(&(objectClass=user)(sAMAccountName={target}))"
    if query_type == "QueryGroup":
        return f"(&(objectClass=group)(cn={target}))"
    if query_type == "EnumerateUsers":
        return "(&(objectCategory=person)(objectClass=user))"
    if query_type == "EnumerateGroups":
        return "(objectClass=group)"
    if query_type == "QueryComputer":
        return f"(&(objectClass=computer)(cn={target}))"
    if query_type == "QueryDomain":
        return f"(&(objectClass=domain)(dc={target.split('.', 1)[0]}))"
    if query_type == "Resolve":
        return f"A {target}"
    return target


@register("IdentityQueryEvents")
def generate(world: World) -> IdentityQueryEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    dc = random.choice(world.domain_controllers)
    timestamp = now_utc()

    idx = random.choices(range(len(_QUERY_VALUES)), weights=_QUERY_WEIGHTS, k=1)[0]
    query_type = _QUERY_VALUES[idx]
    protocol = _QUERY_PROTOCOLS[idx]
    destination_port = _QUERY_PORTS[idx]

    target = _query_target_for_kind(query_type, world)
    query = _ldap_query_string(query_type, target)

    # Map TargetAccount* to a real user when the query is user-scoped, and to
    # the matching DC when it's a domain / computer query — keeps the row
    # consistent with how MDI actually fills these.
    if query_type in ("QueryUser", "EnumerateUsers"):
        target_user = next(
            (u for u in world.users if u.sam_account_name == target),
            random.choice(world.users),
        )
        target_account_display = target_user.display_name
        target_account_upn = target_user.upn
        target_device_name = None
    elif query_type in ("QueryComputer", "QueryDomain", "Resolve"):
        target_account_display = None
        target_account_upn = None
        target_device_name = dc.name
    else:
        target_account_display = None
        target_account_upn = None
        target_device_name = None

    return IdentityQueryEvents(
        AccountDisplayName=user.display_name,
        AccountDomain=world.on_prem_ad_domain,
        AccountName=user.sam_account_name,
        AccountObjectId=user.object_id,
        AccountSid=(
            f"{world.on_prem_sid_prefix}-{user.sid_rid}"
            if user.sid_rid is not None
            else None
        ),
        AccountUpn=user.upn,
        ActionType=f"{protocol} query",
        AdditionalFields=None,
        Application="Active Directory",
        DestinationDeviceName=dc.name,
        DestinationIPAddress=dc.ip,
        DestinationPort=str(destination_port),
        DeviceName=user.device_name,
        IPAddress=ip.ip,
        Location=f"{ip.city}, {ip.country}",
        Port=str(random.randint(49152, 65535)),
        Protocol=protocol,
        Query=query,
        QueryTarget=target,
        QueryType=query_type,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceSystem="Azure",
        TargetAccountDisplayName=target_account_display,
        TargetAccountUpn=target_account_upn,
        TargetDeviceName=target_device_name,
        TenantId=world.tenant_id,
        TimeGenerated=timestamp,
        Type="IdentityQueryEvents",
    )
