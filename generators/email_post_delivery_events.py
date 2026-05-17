from __future__ import annotations

import random

from models import EmailPostDeliveryEvents
from generators.base import register
from generators.common import now_utc
from generators.email_pool import pool_for
from world import World


@register("EmailPostDeliveryEvents")
def generate(world: World) -> EmailPostDeliveryEvents:
    email = pool_for(world).pick()

    # Phishing verdicts → ZAP / admin paths; otherwise any path.
    if email["threat_types"]:
        candidates = [
            p for p in world.email_post_delivery_paths if p.trigger in ("ZAP", "Admin")
        ] or list(world.email_post_delivery_paths)
    else:
        candidates = list(world.email_post_delivery_paths)
    path = random.choice(candidates)

    recipient = email["recipient"]
    timestamp = now_utc()

    return EmailPostDeliveryEvents(
        Action=path.action,
        ActionResult=path.result,
        ActionTrigger=path.trigger,
        ActionType=path.action_type,
        DeliveryLocation=path.delivery_location,
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
