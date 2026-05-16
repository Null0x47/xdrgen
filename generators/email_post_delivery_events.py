from __future__ import annotations

import random

from models import EmailPostDeliveryEvents
from generators.base import register
from generators.common import now_utc
from generators.email_pool import pool_for
from world import World

# Post-delivery actions: ZAP, admin remediation, and user reclassification.
_POST_DELIVERY_PATHS = [
    {
        "action": "Move to junk",
        "action_type": "Phish ZAP",
        "trigger": "ZAP",
        "result": "Success",
        "delivery_location": "JunkFolder",
    },
    {
        "action": "Move to quarantine",
        "action_type": "Phish ZAP",
        "trigger": "ZAP",
        "result": "Success",
        "delivery_location": "Quarantine",
    },
    {
        "action": "Soft delete",
        "action_type": "Manual remediation",
        "trigger": "Admin",
        "result": "Success",
        "delivery_location": "Deleted Items",
    },
    {
        "action": "Hard delete",
        "action_type": "Manual remediation",
        "trigger": "Admin",
        "result": "Success",
        "delivery_location": "Deleted Items",
    },
    {
        "action": "Move to inbox",
        "action_type": "User reported not junk",
        "trigger": "User",
        "result": "Success",
        "delivery_location": "Inbox",
    },
]


@register("EmailPostDeliveryEvents")
def generate(world: World) -> EmailPostDeliveryEvents:
    email = pool_for(world).pick()

    # Phishing verdicts → ZAP / admin paths; otherwise any path.
    if email["threat_types"]:
        path = random.choice(
            [p for p in _POST_DELIVERY_PATHS if p["trigger"] in ("ZAP", "Admin")]
        )
    else:
        path = random.choice(_POST_DELIVERY_PATHS)

    recipient = email["recipient"]
    timestamp = now_utc()

    return EmailPostDeliveryEvents(
        Action=path["action"],
        ActionResult=path["result"],
        ActionTrigger=path["trigger"],
        ActionType=path["action_type"],
        DeliveryLocation=path["delivery_location"],
        DetectionMethods=email["detection_methods"],
        EmailDirection=email["direction"],
        InternetMessageId=email["internet_message_id"],
        NetworkMessageId=email["network_message_id"],
        RecipientEmailAddress=recipient.upn,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SenderFromAddress=email["sender_from_address"],
        SourceSystem="Azure",
        TenantId=world.tenant_id,
        ThreatTypes=email["threat_types"],
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="EmailPostDeliveryEvents",
    )
