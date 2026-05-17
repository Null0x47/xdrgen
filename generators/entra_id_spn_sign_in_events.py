from __future__ import annotations

import random
import uuid

from models import EntraIdSpnSignInEvents
from generators.base import register
from generators.common import now_utc, pick
from world import Resource, WeightedPool, World

# SPN-specific resource fallback used when the profile doesn't set `resources:`.
_DEFAULT_SPN_RESOURCES: WeightedPool[Resource] = WeightedPool(
    random=True,
    entries=(
        Resource(name="Microsoft Graph", id="00000003-0000-0000-c000-000000000000"),
        Resource(
            name="Windows Azure Service Management API",
            id="797f4846-ba00-4fd7-ba43-dac1f8f63013",
        ),
        Resource(name="Azure Key Vault", id="cfa8b339-82a2-471a-a3c9-0fc0be7a4093"),
        Resource(name="Azure Storage", id="e406a681-f3d4-42a8-90b6-c2b029497af1"),
        Resource(name="Azure SQL Database", id="022907d3-0f1b-48f7-badc-1ba6abab6d66"),
        Resource(
            name="Azure Container Registry", id="8b3390db-a8a2-4c39-9c91-45a3a64f54c7"
        ),
    ),
)


@register("EntraIdSpnSignInEvents")
def generate(world: World) -> EntraIdSpnSignInEvents:
    sp = pick(world.service_principals)
    resources = (
        world.resources
        if "resources" in world.model_fields_set
        else _DEFAULT_SPN_RESOURCES
    )
    resource = pick(resources)
    # MIs call from cloud-provider IPs; other SPNs from anywhere.
    if sp.is_managed_identity:
        cloud_ips = tuple(i for i in world.ips if i.category == "Cloud provider")
        ip = random.choice(cloud_ips) if cloud_ips else pick(world.ips)
    else:
        ip = pick(world.ips)
    timestamp = now_utc()

    error_code = pick(world.entra_spn_sign_in_error_codes).code

    return EntraIdSpnSignInEvents(
        Timestamp=timestamp,
        Application=sp.name,
        ApplicationId=sp.app_id,
        IsManagedIdentity=sp.is_managed_identity,
        ErrorCode=error_code,
        CorrelationId=str(uuid.uuid4()),
        ServicePrincipalName=sp.name,
        ServicePrincipalId=sp.id,
        ResourceDisplayName=resource.name,
        ResourceId=resource.id,
        ResourceTenantId=world.tenant_id,
        IPAddress=ip.ip,
        Country=ip.country,
        State=ip.state,
        City=ip.city,
        Latitude=ip.latitude,
        Longitude=ip.longitude,
        RequestId=str(uuid.uuid4()),
        ReportId=str(random.randint(10**15, 10**16 - 1)),
    )
