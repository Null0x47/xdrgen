from __future__ import annotations

import random
import uuid

from models import EntraIdSpnSignInEvents
from generators.base import register
from generators.common import now_utc
from world import World

# Service principals that sign in to access tenant resources. Mix of
# user-assigned and system-assigned managed identities and regular SPNs.
_SERVICE_PRINCIPALS = [
    {
        "name": "contoso-app-prod",
        "id": "b7c1f4e2-0d8a-4d7e-9c2b-1a3f5e6c7d8a",
        "app_id": "f2c5d6e7-8a9b-4c1d-bf2e-3a4b5c6d7e8f",
        "is_managed_identity": False,
    },
    {
        "name": "contoso-functions-mi",
        "id": "c8d2e5f3-1e9b-4f8e-ad3c-2b4f6e7d8a9b",
        "app_id": "0a1b2c3d-4e5f-4061-8273-849a5b6c7d8e",
        "is_managed_identity": True,
    },
    {
        "name": "contoso-aks-system-mi",
        "id": "d9e3f604-2f0c-4a09-be4d-3c5f7a8b9c0d",
        "app_id": "1b2c3d4e-5f60-4172-9384-95a6b7c8d9ef",
        "is_managed_identity": True,
    },
    {
        "name": "github-actions-deploy",
        "id": "e0f4a715-3a1d-4b1a-cf5e-4d607b8c9d0e",
        "app_id": "2c3d4e5f-6071-4283-a495-b6c7d8e9f012",
        "is_managed_identity": False,
    },
    {
        "name": "terraform-cloud-runner",
        "id": "f105b826-4b2e-4c2b-d06f-5e718c9d0e1f",
        "app_id": "3d4e5f60-7182-4394-b5a6-c7d8e9f01223",
        "is_managed_identity": False,
    },
]

# Resources commonly accessed by service principals — Azure plane, Graph,
# Key Vault, Storage, ARM. ResourceId values are first-party app IDs.
_RESOURCES = [
    {"name": "Microsoft Graph", "id": "00000003-0000-0000-c000-000000000000"},
    {
        "name": "Windows Azure Service Management API",
        "id": "797f4846-ba00-4fd7-ba43-dac1f8f63013",
    },
    {"name": "Azure Key Vault", "id": "cfa8b339-82a2-471a-a3c9-0fc0be7a4093"},
    {"name": "Azure Storage", "id": "e406a681-f3d4-42a8-90b6-c2b029497af1"},
    {"name": "Azure SQL Database", "id": "022907d3-0f1b-48f7-badc-1ba6abab6d66"},
    {"name": "Azure Container Registry", "id": "8b3390db-a8a2-4c39-9c91-45a3a64f54c7"},
]


@register("EntraIdSpnSignInEvents")
def generate(world: World) -> EntraIdSpnSignInEvents:
    sp = random.choice(_SERVICE_PRINCIPALS)
    resource = random.choice(_RESOURCES)
    # Managed identities call from inside the Microsoft cloud network — biased
    # toward the cloud-provider IPs in the pool. Regular SPNs (CI runners,
    # Terraform workers, external automation) come from anywhere.
    if sp["is_managed_identity"]:
        candidates = (
            tuple(i for i in world.ips if i.category == "Cloud provider") or world.ips
        )
    else:
        candidates = world.ips
    ip = random.choice(candidates)
    timestamp = now_utc()

    error_code = random.choices(
        world.entra_spn_sign_in_error_codes,
        weights=[c.weight for c in world.entra_spn_sign_in_error_codes],
        k=1,
    )[0].code

    return EntraIdSpnSignInEvents(
        Timestamp=timestamp,
        Application=sp["name"],
        ApplicationId=sp["app_id"],
        IsManagedIdentity=sp["is_managed_identity"],
        ErrorCode=error_code,
        CorrelationId=str(uuid.uuid4()),
        ServicePrincipalName=sp["name"],
        ServicePrincipalId=sp["id"],
        ResourceDisplayName=resource["name"],
        ResourceId=resource["id"],
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
