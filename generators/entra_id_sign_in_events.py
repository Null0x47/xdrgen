from __future__ import annotations

import json
import random
import uuid
from datetime import timedelta

from models import EntraIdSignInEvents
from generators.base import register
from generators.common import now_utc
from world import ConditionalAccessPolicy, World


def _conditional_access_payload(
    policies: tuple[ConditionalAccessPolicy, ...], success: bool
) -> tuple[str, int]:
    """Return (json-encoded policies string, ConditionalAccessStatus)."""
    if not policies:
        return "[]", 0 if success else 2
    sample = random.sample(policies, k=random.randint(1, len(policies)))
    if success:
        status = 0  # success / applied
        result = "success"
    else:
        # 1 = failure to apply, 2 = not applied (e.g. block / interrupted)
        status = random.choice([1, 2])
        result = "failure" if status == 1 else "notApplied"
    payload = [
        {
            "id": p.id,
            "displayName": p.displayName,
            "enforcedGrantControls": list(p.enforcedGrantControls),
            "enforcedSessionControls": list(p.enforcedSessionControls),
            "result": result,
        }
        for p in sample
    ]
    return json.dumps(payload, separators=(",", ":")), status


@register("EntraIdSignInEvents")
def generate(world: World) -> EntraIdSignInEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    ua = random.choice(world.user_agents)
    app = random.choice(world.client_apps)
    resource = random.choice(world.resources)
    timestamp = now_utc()

    error_entry = random.choices(
        world.entra_sign_in_error_codes,
        weights=[c.weight for c in world.entra_sign_in_error_codes],
        k=1,
    )[0]
    error_code = error_entry.code
    success = error_code == 0

    # Logon type — service / app accounts are more often non-interactive.
    if user.type == "Application":
        logon_type = "nonInteractiveUser"
    else:
        logon_type = random.choices(
            ["interactiveUser", "nonInteractiveUser"],
            weights=[7, 3],
            k=1,
        )[0]

    # Browser sign-ins via web come from Browser client app; Outlook UA
    # implies a desktop client; mobile UA implies the mobile app.
    if "Mobile" in ua.device_type:
        client_app_used = "Mobile Apps and Desktop clients"
    elif "Outlook" in ua.browser:
        client_app_used = "Modern Authentication Clients"
    else:
        client_app_used = "Browser"

    # Device association: only some users have a registered device, and we
    # only attach it ~70% of the time even when they do.
    has_device = user.device_id is not None and random.random() < 0.7
    device_name = user.device_name if has_device else None
    device_id = user.device_id if has_device else None
    device_trust_type = random.choice(["AzureAd", "Workplace"]) if has_device else None
    is_managed = 1 if has_device else 0
    is_compliant = 1 if has_device and random.random() < 0.85 else 0

    is_external = 1 if "#EXT#" in user.upn else 0
    is_guest = is_external == 1
    is_confidential_client = user.type == "Application"

    # Risk telemetry — usually clean, occasionally elevated.
    if success and random.random() < 0.95:
        risk_level = 0
        risk_state = 0
        risk_details = 0
    else:
        risk_level = random.choice([10, 50, 100])
        risk_state = random.choice([4, 5])
        risk_details = random.choice([1, 2, 3])

    auth_requirement = (
        "multiFactorAuthentication"
        if random.random() < 0.7
        else "singleFactorAuthentication"
    )

    ca_policies, ca_status = _conditional_access_payload(
        world.conditional_access_policies, success
    )

    network_location = (
        '["trustedNamedLocation"]' if ip.category == "Corporate" else "[]"
    )

    correlation_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    last_pwd_change = timestamp - timedelta(days=user.last_password_change_days_ago)
    alt_sign_in = (
        user.upn.replace("@contoso.com", "@corp.contoso.local")
        if user.upn.endswith("@contoso.com")
        else None
    )

    return EntraIdSignInEvents(
        Timestamp=timestamp,
        Application=app.name,
        ApplicationId=app.app_id,
        LogonType=logon_type,
        ErrorCode=error_code,
        CorrelationId=correlation_id,
        SessionId=str(uuid.uuid4()),
        AccountDisplayName=user.display_name,
        AccountObjectId=user.object_id,
        AccountUpn=user.upn,
        IsConfidentialClient=is_confidential_client,
        IsExternalUser=is_external,
        IsGuestUser=is_guest,
        AlternateSignInName=alt_sign_in,
        LastPasswordChangeTimestamp=last_pwd_change,
        ResourceDisplayName=resource.name,
        ResourceId=resource.id,
        ResourceTenantId=world.tenant_id,
        DeviceName=device_name,
        EntraIdDeviceId=device_id,
        OSPlatform=ua.platform,
        DeviceTrustType=device_trust_type,
        IsManaged=is_managed,
        IsCompliant=is_compliant,
        AuthenticationProcessingDetails=(
            "Primary authentication completed; token issued."
            if success
            else (
                error_entry.description
                or f"Authentication failed with error {error_code}."
            )
        ),
        AuthenticationRequirement=auth_requirement,
        TokenIssuerType=0,
        RiskLevelAggregated=risk_level,
        RiskDetails=risk_details,
        RiskState=risk_state,
        UserAgent=ua.ua,
        ClientAppUsed=client_app_used,
        Browser=ua.browser,
        ConditionalAccessPolicies=ca_policies,
        ConditionalAccessStatus=ca_status,
        IPAddress=ip.ip,
        Country=ip.country,
        State=ip.state,
        City=ip.city,
        Latitude=ip.latitude,
        Longitude=ip.longitude,
        NetworkLocationDetails=network_location,
        RequestId=request_id,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        EndpointCall="oauth2/v2.0/token",
    )
