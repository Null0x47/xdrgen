from __future__ import annotations

import random
import uuid

from models import CloudAppEvents
from generators.base import register
from generators.common import now_utc
from world import User, World

# ApplicationId / actions sourced from the Defender for Cloud Apps catalogue.
_APPS = [
    {
        "name": "Microsoft 365",
        "app_id": 11161,
        "instance_id": 1001,
        "audit_source": "Office 365",
        "actions": [
            "FileAccessed",
            "FileDownloaded",
            "FileUploaded",
            "FileModified",
            "FileDeleted",
            "FileSyncDownloadedFull",
            "FileSyncUploadedFull",
            "SharingSet",
            "AnonymousLinkCreated",
        ],
    },
    {
        "name": "Microsoft Exchange Online",
        "app_id": 20893,
        "instance_id": 1002,
        "audit_source": "Office 365",
        "actions": [
            "MailItemsAccessed",
            "Send",
            "Update",
            "MoveToDeletedItems",
            "SoftDelete",
            "HardDelete",
            "New-InboxRule",
            "Set-Mailbox",
        ],
    },
    {
        "name": "Microsoft Teams",
        "app_id": 28375,
        "instance_id": 1003,
        "audit_source": "Office 365",
        "actions": [
            "MessageSent",
            "MemberAdded",
            "MemberRemoved",
            "TeamCreated",
            "ChannelAdded",
            "MeetingDetail",
        ],
    },
    {
        "name": "Salesforce",
        "app_id": 11114,
        "instance_id": 1004,
        "audit_source": "Salesforce",
        "actions": [
            "Login",
            "Logout",
            "ReportRun",
            "RecordExported",
            "ApiCall",
            "PasswordChange",
        ],
    },
    {
        "name": "Box",
        "app_id": 10489,
        "instance_id": 1005,
        "audit_source": "Box",
        "actions": [
            "FILE_PREVIEW",
            "DOWNLOAD",
            "UPLOAD",
            "DELETE",
            "SHARE",
            "COLLABORATION_INVITE",
        ],
    },
    {
        "name": "GitHub",
        "app_id": 15760,
        "instance_id": 1006,
        "audit_source": "GitHub",
        "actions": [
            "git.clone",
            "git.push",
            "repo.access",
            "repo.create",
            "oauth_authorization.create",
            "personal_access_token.create",
        ],
    },
]

_FILE_NAMES = [
    "Q3_forecast.xlsx",
    "design-spec.docx",
    "customer_list.csv",
    "demo-deck.pptx",
    "build_logs.txt",
    "release-notes.md",
    "contract_v3.pdf",
    "audit_export.zip",
]
_MAIL_SUBJECTS = [
    "Re: Q3 numbers",
    "FW: NDA draft",
    "Weekly status",
    "Action required: account review",
    "Calendar invite: planning sync",
]


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
        object_name = random.choice(_FILE_NAMES)
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
        object_name = random.choice(_MAIL_SUBJECTS)
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
        object_name = random.choice(
            ["Engineering", "Finance", "Sales-EMEA", "All Hands"]
        )
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
    user = random.choice(world.users)
    app = random.choice(_APPS)
    ip = random.choice(world.ips)
    ua = random.choice(world.user_agents)
    action = random.choice(app["actions"])
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
        "RecordType": app["app_id"],
        "ResultStatus": "Succeeded",
        "UserKey": user.object_id,
        "UserType": 0 if user.type == "Regular" else 2,
        "Version": 1,
        "Workload": app["name"],
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
        AppInstanceId=app["instance_id"],
        Application=app["name"],
        ApplicationId=app["app_id"],
        AuditSource=app["audit_source"],
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
        TimeGenerated=timestamp,
        Type="CloudAppEvents",
        UncommonForUser=[],
        UserAgent=ua.ua,
        UserAgentTags=[],
    )
