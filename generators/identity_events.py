from __future__ import annotations

import random
import uuid

from models import IdentityEvents
from generators.base import register
from generators.common import now_utc, pick
from world import User, World


def _target_objects(kind: str, user: User, world: World) -> list[dict]:
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
                "Name": pick(world.identity_event_group_names).value,
                "Id": str(uuid.uuid4()),
            }
        ]
    if kind == "app":
        return [
            {
                "Type": "application",
                "Name": pick(world.identity_event_app_names).value,
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
    user = pick(world.users)
    ip = pick(world.ips)
    ua = pick(world.user_agents)
    timestamp = now_utc()

    raw = pick(world.identity_raw_actions)
    action_type, application, target_kind = raw.action, raw.application, raw.target_kind
    target_objects = _target_objects(target_kind, user, world)

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
