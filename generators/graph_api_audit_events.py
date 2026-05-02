"""Generator for `GraphApiAuditEvents` — Microsoft Graph API audit telemetry.

Each row models a single Graph API call: who called it, which endpoint, which
HTTP method, the OAuth scope on the token, the workload that owns the
endpoint, and the HTTP outcome. Two call shapes are produced:

  * Delegated (user-context) calls — `EntityType=User`, `AccountObjectId`
    set to the signing-in user, `ServicePrincipalId` set to the client app
    the user authenticated through.
  * App-only (client_credentials) calls — `EntityType=ServicePrincipal`,
    `AccountObjectId` empty, `ServicePrincipalId` and `ApplicationId` both
    pointing at the calling app.

This mirrors how the same call appears in real Defender XDR data.
"""

from __future__ import annotations

import random
import uuid

from models import GraphApiAuditEvents
from generators.base import register
from generators.common import now_utc
from world import World

# Real Microsoft Graph endpoints. Each entry pairs a URI template with the
# HTTP method, the workload that owns it, and the OAuth scope a token would
# carry to access it. Path placeholders are substituted at runtime so each
# event carries a fresh, well-formed Graph URL.
_ENDPOINTS: tuple[dict[str, str], ...] = (
    {
        "method": "GET",
        "uri": "/{ver}/users",
        "workload": "Microsoft.DirectoryServices",
        "scope": "User.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/users/{user_id}",
        "workload": "Microsoft.DirectoryServices",
        "scope": "User.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/users/{user_id}/manager",
        "workload": "Microsoft.DirectoryServices",
        "scope": "User.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/users/{user_id}/memberOf",
        "workload": "Microsoft.DirectoryServices",
        "scope": "GroupMember.Read.All",
    },
    {
        "method": "PATCH",
        "uri": "/{ver}/users/{user_id}",
        "workload": "Microsoft.DirectoryServices",
        "scope": "User.ReadWrite.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/groups",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Group.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/groups/{group_id}/members",
        "workload": "Microsoft.DirectoryServices",
        "scope": "GroupMember.Read.All",
    },
    {
        "method": "POST",
        "uri": "/{ver}/groups/{group_id}/members/$ref",
        "workload": "Microsoft.DirectoryServices",
        "scope": "GroupMember.ReadWrite.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/applications",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Application.Read.All",
    },
    {
        "method": "POST",
        "uri": "/{ver}/applications",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Application.ReadWrite.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/servicePrincipals",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Application.Read.All",
    },
    {
        "method": "POST",
        "uri": "/{ver}/servicePrincipals/{sp_id}/addPassword",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Application.ReadWrite.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/directoryRoles",
        "workload": "Microsoft.DirectoryServices",
        "scope": "RoleManagement.Read.Directory",
    },
    {
        "method": "POST",
        "uri": "/{ver}/directoryRoles/{role_id}/members/$ref",
        "workload": "Microsoft.DirectoryServices",
        "scope": "RoleManagement.ReadWrite.Directory",
    },
    {
        "method": "GET",
        "uri": "/{ver}/identity/conditionalAccess/policies",
        "workload": "Microsoft.DirectoryServices",
        "scope": "Policy.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/me/messages",
        "workload": "Microsoft.Exchange",
        "scope": "Mail.Read",
    },
    {
        "method": "POST",
        "uri": "/{ver}/me/sendMail",
        "workload": "Microsoft.Exchange",
        "scope": "Mail.Send",
    },
    {
        "method": "GET",
        "uri": "/{ver}/me/calendar/events",
        "workload": "Microsoft.Exchange",
        "scope": "Calendars.Read",
    },
    {
        "method": "GET",
        "uri": "/{ver}/sites/root/drives",
        "workload": "Microsoft.SharePoint",
        "scope": "Files.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/drives/{drive_id}/root/children",
        "workload": "Microsoft.SharePoint",
        "scope": "Files.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/teams/{team_id}/channels",
        "workload": "Microsoft.Teams",
        "scope": "Channel.ReadBasic.All",
    },
    {
        "method": "POST",
        "uri": "/{ver}/chats/{chat_id}/messages",
        "workload": "Microsoft.Teams",
        "scope": "Chat.ReadWrite",
    },
    {
        "method": "GET",
        "uri": "/{ver}/auditLogs/signIns",
        "workload": "Microsoft.Reports",
        "scope": "AuditLog.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/auditLogs/directoryAudits",
        "workload": "Microsoft.Reports",
        "scope": "AuditLog.Read.All",
    },
    {
        "method": "GET",
        "uri": "/{ver}/security/alerts_v2",
        "workload": "Microsoft.Security",
        "scope": "SecurityAlert.Read.All",
    },
    {
        "method": "POST",
        "uri": "/{ver}/security/runHuntingQuery",
        "workload": "Microsoft.Security",
        "scope": "ThreatHunting.Read.All",
    },
)

# HTTP outcomes. Successful 2xx codes dominate; the failure tail covers the
# four codes a SOC analyst actually looks for in Graph traffic — auth
# (401), permission (403), missing target (404), throttle (429) — plus a
# token of 5xx errors.
_STATUS_CODES: tuple[tuple[str, int], ...] = (
    ("200", 80),
    ("201", 4),
    ("204", 4),
    ("400", 2),
    ("401", 2),
    ("403", 3),
    ("404", 2),
    ("429", 2),
    ("500", 1),
)
_STATUS_VALUES, _STATUS_WEIGHTS = zip(*_STATUS_CODES)


# Azure regions where graph.microsoft.com requests typically terminate.
_LOCATIONS: tuple[str, ...] = (
    "westeurope",
    "northeurope",
    "eastus",
    "westus2",
    "southeastasia",
    "uksouth",
)


@register("GraphApiAuditEvents")
def generate(world: World) -> GraphApiAuditEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    endpoint = random.choice(_ENDPOINTS)
    api_version = random.choice(("v1.0", "beta"))
    timestamp = now_utc()

    # ~60% of human users issue delegated calls; service accounts always go
    # through app-only flows. In delegated flow, both AccountObjectId (the
    # user) and ServicePrincipalId (the app the user signed in through) are
    # populated. In app-only flow, only the SPN is — and ApplicationId
    # equals ServicePrincipalId because the app *is* its own caller.
    delegated = user.type != "Application" and random.random() < 0.6
    if delegated:
        entity_type = "User"
        account_object_id = user.object_id
        client = random.choice(world.client_apps)
        application_id = client.app_id
        service_principal_id = client.app_id
    else:
        entity_type = "ServicePrincipal"
        account_object_id = None
        client = random.choice(world.client_apps)
        application_id = client.app_id
        service_principal_id = client.app_id

    group = random.choice(world.groups)
    uri_path = endpoint["uri"].format(
        ver=api_version,
        user_id=user.object_id,
        group_id=group.id,
        sp_id=service_principal_id,
        role_id=str(uuid.uuid4()),
        drive_id=f"b!{uuid.uuid4().hex[:22]}",
        team_id=str(uuid.uuid4()),
        chat_id=f"19:meeting_{uuid.uuid4().hex[:16]}@thread.v2",
    )
    request_uri = f"https://graph.microsoft.com{uri_path}"

    status_code = random.choices(_STATUS_VALUES, weights=_STATUS_WEIGHTS, k=1)[0]
    is_success = status_code.startswith("2")

    # Reads on success return real payloads; writes return small confirmations;
    # 204 No Content returns 0; failures return short error envelopes.
    if not is_success:
        response_size = random.randint(80, 600)
    elif status_code == "204":
        response_size = 0
    elif endpoint["method"] == "GET":
        response_size = random.randint(800, 60_000)
    else:
        response_size = random.randint(300, 3_000)

    return GraphApiAuditEvents(
        IdentityProvider=f"https://sts.windows.net/{world.tenant_id}/",
        ApiVersion=api_version,
        ApplicationId=application_id,
        IPAddress=ip.ip,
        ClientRequestId=str(uuid.uuid4()),
        EntityType=entity_type,
        RequestUri=request_uri,
        AccountObjectId=account_object_id,
        OperationId=str(uuid.uuid4()),
        Location=random.choice(_LOCATIONS),
        RequestDuration=str(random.randint(20, 1500)),
        RequestId=str(uuid.uuid4()),
        RequestMethod=endpoint["method"],
        Timestamp=timestamp.isoformat(),
        ResponseStatusCode=status_code,
        Scopes=endpoint["scope"],
        UniqueTokenIdentifier=uuid.uuid4().hex,
        TargetWorkload=endpoint["workload"],
        ServicePrincipalId=service_principal_id,
        ResponseSize=response_size,
    )
