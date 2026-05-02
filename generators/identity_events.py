from __future__ import annotations

import random
import uuid

from models import IdentityEvents
from generators.base import register
from generators.common import now_utc
from world import User, World

# IdentityEvents is the unified Sentinel SecurityIQ table — fed by many
# source applications, not just AD. ActionType here is the *raw* value from
# the source, not a normalised enum. (action, application, target_kind).
_RAW_ACTIONS = [
    ("UserLoggedIn", "AzureActiveDirectory", "user"),
    ("UserLoginFailed", "AzureActiveDirectory", "user"),
    ("Add user.", "AzureActiveDirectory", "user"),
    ("Delete user.", "AzureActiveDirectory", "user"),
    ("Update user.", "AzureActiveDirectory", "user"),
    ("Add member to group.", "AzureActiveDirectory", "group"),
    ("Remove member from group.", "AzureActiveDirectory", "group"),
    ("Reset user password.", "AzureActiveDirectory", "user"),
    ("Add app role assignment to service principal.", "AzureActiveDirectory", "app"),
    ("Consent to application.", "AzureActiveDirectory", "app"),
    ("login", "Okta", "user"),
    ("user.session.start", "Okta", "user"),
    ("group.user_membership.add", "Okta", "group"),
    ("policy.lifecycle.update", "Okta", "policy"),
]

_GROUP_NAMES = [
    "Engineering",
    "Finance",
    "Sales",
    "Domain Admins",
    "All Employees",
    "Sales-EMEA",
]
_APP_NAMES = [
    "Salesforce",
    "Box",
    "Workday",
    "ServiceNow",
    "GitHub",
]


def _target_objects(kind: str, user: User) -> list[dict]:
    if kind == "user":
        return [
            {
                "Type": "user",
                "Name": user.upn,
                "Id": user.object_id,
            }
        ]
    if kind == "group":
        return [
            {
                "Type": "group",
                "Name": random.choice(_GROUP_NAMES),
                "Id": str(uuid.uuid4()),
            }
        ]
    if kind == "app":
        return [
            {
                "Type": "application",
                "Name": random.choice(_APP_NAMES),
                "Id": str(uuid.uuid4()),
            }
        ]
    return [
        {
            "Type": kind,
            "Name": kind,
            "Id": str(uuid.uuid4()),
        }
    ]


@register("IdentityEvents")
def generate(world: World) -> IdentityEvents:
    user = random.choice(world.users)
    ip = random.choice(world.ips)
    ua = random.choice(world.user_agents)
    timestamp = now_utc()

    action_type, application, target_kind = random.choice(_RAW_ACTIONS)
    target_objects = _target_objects(target_kind, user)

    # Failures are signalled both by the ActionType ("…Failed") and by an
    # explicit ActionResult so consumers can pivot on either.
    failed = "Failed" in action_type or "fail" in action_type.lower()
    action_result = "Failure" if failed else "Success"
    failure_reason = "InvalidCredentials" if failed else None

    instance_id = (
        "contoso.okta.com" if application == "Okta" else "contoso.onmicrosoft.com"
    )

    raw_event_id = str(uuid.uuid4())
    raw_event = {
        "id": raw_event_id,
        "operationName": action_type,
        "result": action_result,
        "initiatedBy": {
            "user": {
                "id": user.object_id,
                "userPrincipalName": user.upn,
                "displayName": user.display_name,
            }
        },
        "targetResources": target_objects,
        "ipAddress": ip.ip,
    }

    return IdentityEvents(
        Timestamp=timestamp,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        AccountId=user.object_id,
        AccountType=user.type,
        AccountDisplayName=user.display_name,
        AccountUpn=user.upn,
        ActionType=action_type,
        ActionResult=action_result,
        ActionFailureReason=failure_reason,
        IPAddress=ip.ip,
        UserAgent=ua.ua,
        TargetObjects=target_objects,
        Application=application,
        ApplicationInstanceId=instance_id,
        ApplicationEventId=raw_event_id,
        ApplicationSessionId=str(uuid.uuid4()),
        RawEventData=raw_event,
        AdditionalFields={},
    )
