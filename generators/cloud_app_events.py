from __future__ import annotations

import random
import uuid

from models import CloudAppEvents
from generators.base import register
from generators.common import now_utc, pick
from world import User, World


def _activity_objects(
    action: str, user: User, world: World
) -> tuple[str, str, str, list[dict]]:
    a = action.lower()
    if any(
        k in a
        for k in (
            "file",
            "download",
            "upload",
            "preview",
            "sharing",
            "anonymouslink",
            "git.",
        )
    ):
        object_type = "File"
        object_name = pick(world.cloud_app_file_names).value
        object_id = str(uuid.uuid4())
        return (
            object_type,
            object_name,
            object_id,
            [{"Type": object_type, "Name": object_name, "Id": object_id}],
        )
    if any(
        k in a for k in ("mail", "send", "delete", "move", "inboxrule", "set-mailbox")
    ):
        object_type = "Email"
        object_name = pick(world.cloud_app_mail_subjects).value
        object_id = f"<{uuid.uuid4()}@{world.tenant_domain}>"
        return (
            object_type,
            object_name,
            object_id,
            [{"Type": object_type, "Subject": object_name, "Id": object_id}],
        )
    if "login" in a or "logon" in a or "logout" in a:
        object_type = "Account"
        return (
            object_type,
            user.upn,
            user.object_id,
            [{"Type": object_type, "Name": user.upn, "Id": user.object_id}],
        )
    if any(k in a for k in ("member", "team", "channel", "collaboration_invite")):
        object_type = "Group"
        object_name = pick(world.cloud_app_group_names).value
        object_id = str(uuid.uuid4())
        return (
            object_type,
            object_name,
            object_id,
            [{"Type": object_type, "Name": object_name, "Id": object_id}],
        )
    object_type = "Other"
    object_name = action
    object_id = str(uuid.uuid4())
    return (
        object_type,
        object_name,
        object_id,
        [{"Type": object_type, "Name": object_name, "Id": object_id}],
    )


@register("CloudAppEvents")
def generate(world: World) -> CloudAppEvents:
    user = pick(world.users)
    app = pick(world.cloud_apps)
    ip = pick(world.ips)
    ua = pick(world.user_agents)
    action = random.choice(app.actions)
    timestamp = now_utc()

    is_admin_op = user.type == "Admin" and random.random() < 0.4
    is_external = "#EXT#" in user.upn
    is_anon_proxy = ip.category == "ISP" and random.random() < 0.05

    object_type, object_name, object_id, activity_objects = _activity_objects(
        action, user, world
    )

    raw = {
        "CreationTime": timestamp.isoformat(),
        "Id": str(uuid.uuid4()),
        "Operation": action,
        "OrganizationId": world.tenant_id,
        "RecordType": app.app_id,
        "ResultStatus": "Succeeded",
        "UserKey": user.object_id,
        "UserType": 0 if user.type == "Regular" else 2,
        "Version": 1,
        "Workload": app.name,
        "ClientIP": ip.ip,
        "UserId": user.upn,
        "ObjectId": object_id,
    }

    return CloudAppEvents(
        AccountDisplayName=user.display_name,
        AccountId=user.upn,
        AccountObjectId=user.object_id,
        AccountType=user.type,
        ActionType=action,
        ActivityObjects=activity_objects,
        ActivityType=action,
        AdditionalFields={},
        AppInstanceId=app.instance_id,
        Application=app.name,
        ApplicationId=app.app_id,
        AuditSource=app.audit_source,
        City=ip.city,
        CountryCode=ip.country,
        DeviceType=ua.device_type,
        IPAddress=ip.ip,
        IPCategory=ip.category,
        IPTags=[],
        IsAdminOperation=is_admin_op,
        IsAnonymousProxy=is_anon_proxy,
        IsExternalUser=is_external,
        IsImpersonated=False,
        ISP=ip.isp,
        LastSeenForUser={
            "IPAddress": random.randint(0, 30),
            "CountryCode": random.randint(0, 90),
            "ISP": random.randint(0, 30),
            "UserAgent": random.randint(0, 30),
        },
        OAuthAppId=None,
        ObjectId=object_id,
        ObjectName=object_name,
        ObjectType=object_type,
        OSPlatform=ua.platform,
        RawEventData=raw,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SessionData={"SessionId": str(uuid.uuid4())},
        SourceSystem="Azure",
        TenantId=world.tenant_id,
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="CloudAppEvents",
        UncommonForUser=[],
        UserAgent=ua.ua,
        UserAgentTags=[],
    )
