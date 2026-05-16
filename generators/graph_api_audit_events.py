"""GraphApiAuditEvents generator — emits delegated and app-only Graph calls."""

from __future__ import annotations

import random
import re
import uuid

from models import GraphApiAuditEvents
from generators.base import register
from generators.common import now_utc
from world import World

# Weighted HTTP outcomes — 2xx dominates; failure tail covers 401/403/404/429.
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


_PINNED_VERSION_RE = re.compile(r"^/(v1\.0|beta)/")


@register("GraphApiAuditEvents")
def generate(world: World) -> GraphApiAuditEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    endpoint = random.choice(world.graph_api_endpoints)
    timestamp = now_utc()

    # ~60% delegated for humans; service accounts always app-only.
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
    device = random.choice(world.devices)
    # Pin ApiVersion if the URI hard-codes one; else randomise.
    pinned = _PINNED_VERSION_RE.match(endpoint.uri)
    api_version = pinned.group(1) if pinned else random.choice(("v1.0", "beta"))
    uri_path = endpoint.uri.format(
        ver=api_version,
        user_id=user.object_id,
        group_id=group.id,
        sp_id=service_principal_id,
        app_id=application_id,
        device_id=device.device_id,
        role_id=str(uuid.uuid4()),
        drive_id=f"b!{uuid.uuid4().hex[:22]}",
        team_id=str(uuid.uuid4()),
        chat_id=f"19:meeting_{uuid.uuid4().hex[:16]}@thread.v2",
    )
    request_uri = f"https://graph.microsoft.com{uri_path}"

    status_code = random.choices(_STATUS_VALUES, weights=_STATUS_WEIGHTS, k=1)[0]
    is_success = status_code.startswith("2")

    # GETs return larger payloads than writes; 204 = 0; failures = short envelopes.
    if not is_success:
        response_size = random.randint(80, 600)
    elif status_code == "204":
        response_size = 0
    elif endpoint.method == "GET":
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
        Location=random.choice(world.graph_api_locations),
        RequestDuration=str(random.randint(20, 1500)),
        RequestId=str(uuid.uuid4()),
        RequestMethod=endpoint.method,
        Timestamp=timestamp.isoformat(),
        ResponseStatusCode=status_code,
        Scopes=endpoint.scope,
        UniqueTokenIdentifier=uuid.uuid4().hex,
        TargetWorkload=endpoint.workload,
        ServicePrincipalId=service_principal_id,
        ResponseSize=response_size,
    )
