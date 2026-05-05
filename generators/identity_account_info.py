from __future__ import annotations

import random
import uuid
from datetime import timedelta

from models import IdentityAccountInfo
from generators.base import register
from generators.common import now_utc
from world import World

_AUTH_METHODS = ["Credentials", "Federated", "Hybrid"]


def _source_providers(world: World) -> list[tuple[str, str, str]]:
    """Identity providers Defender ingests profile data from."""
    return [
        ("Microsoft Entra ID", world.tenant_id, "Contoso"),
        ("Active Directory", world.on_prem_ad_domain, "Contoso AD"),
        ("Okta", "contoso.okta.com", "Contoso Okta"),
    ]


_DEFENDER_RISK_LEVELS = [
    (0, 80),  # None
    (1, 12),  # Low
    (2, 6),  # Medium
    (3, 2),  # High
]
_RISK_VALUES, _RISK_WEIGHTS = zip(*_DEFENDER_RISK_LEVELS)


@register("IdentityAccountInfo")
def generate(world: World) -> IdentityAccountInfo:
    user = random.choice(world.users)
    provider, provider_instance_id, provider_display = random.choice(
        _source_providers(world)
    )
    timestamp = now_utc()

    risk_level = random.choices(_RISK_VALUES, weights=_RISK_WEIGHTS, k=1)[0]
    is_admin = user.type == "Admin"
    is_service = user.type == "Application"
    is_guest = "#EXT#" in user.upn

    # 90% strong-identifier matches; 10% human-linked.
    if random.random() < 0.9:
        link_type = "Strong identifiers"
        link_reason = "Matched on objectId + UPN"
        link_by = "System"
    else:
        link_type = "Manual"
        link_reason = "Linked by SOC during account merge"
        link_by = "sam.rivera@contoso.com"

    last_pwd_change = timestamp - timedelta(days=user.last_password_change_days_ago)

    enrolled_mfas = (
        []
        if is_service
        else [
            {"Type": "MicrosoftAuthenticator", "Status": "Active"},
            {"Type": "Sms", "Status": "Active"},
        ]
    )

    assigned_roles = (
        ["62e90394-69f5-4237-9190-012177145e10"]  # Global Administrator
        if is_admin
        else []
    )
    eligible_roles = (
        ["fe930be7-5e62-47db-91af-98c3a49a38b1"]  # User Administrator
        if is_admin
        else []
    )

    tags = []
    if is_admin:
        tags.append("Sensitive")
    if is_service:
        tags.append("Service Account")
    if is_guest:
        tags.append("Guest")

    return IdentityAccountInfo(
        Timestamp=timestamp,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceProviderAccountId=user.object_id,
        AccountId=str(uuid.uuid4()),
        IdentityId=str(uuid.uuid4()),
        IsPrimary=True,
        IdentityLinkType=link_type,
        IdentityLinkReason=link_reason,
        IdentityLinkTime=timestamp - timedelta(days=random.randint(30, 720)),
        IdentityLinkBy=link_by,
        DisplayName=user.display_name,
        AccountUpn=user.upn,
        EmailAddress=user.upn if "@" in user.upn and "#EXT#" not in user.upn else None,
        CriticalityLevel=4 if is_admin else 2,
        DefenderRiskLevel=risk_level,
        DefenderRiskUpdateTime=timestamp - timedelta(hours=random.randint(0, 72)),
        Type="ServiceAccount" if is_service else "User",
        GivenName=user.given_name,
        Surname=user.surname,
        EmployeeId=user.employee_id,
        Department=user.department,
        JobTitle=user.job_title,
        Address=None,
        City=user.city,
        Country=user.country,
        Phone=None,
        Manager=(
            "sam.rivera@contoso.com"
            if user.upn != "sam.rivera@contoso.com" and not is_service
            else None
        ),
        Sid=(
            f"{world.on_prem_sid_prefix}-{user.sid_rid}"
            if user.sid_rid is not None
            else None
        ),
        AccountStatus="Enabled",
        SourceProvider=provider,
        SourceProviderInstanceId=provider_instance_id,
        SourceProviderInstanceDisplayName=provider_display,
        AuthenticationMethod=random.choice(_AUTH_METHODS),
        AuthenticationSourceAcccountId=None,
        EnrolledMfas=enrolled_mfas,
        LastPasswordChangeTime=last_pwd_change,
        GroupMembership=[str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
        AssignedRoles=assigned_roles,
        EligibleRoles=eligible_roles,
        TenantMembershipType="Guest" if is_guest else "Member",
        CreatedDateTime=timestamp - timedelta(days=random.randint(180, 1500)),
        DeletedDateTime=None,
        Tags=tags,
        SourceProvderRiskLevel=(
            random.choice(["Low", "Medium", "High"]) if risk_level >= 2 else "Low"
        ),
        AdditionalFields={},
        TenantId=world.tenant_id,
    )
