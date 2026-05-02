from __future__ import annotations

import random

from models import EmailAttachmentInfo
from generators.base import register
from generators.common import now_utc
from generators.email_corpus import corpus_for
from world import World


@register("EmailAttachmentInfo")
def generate(world: World) -> EmailAttachmentInfo:
    email = corpus_for(world).pick_with_attachments()
    attachment = random.choice(email["attachments"])
    recipient = email["recipient"]
    timestamp = now_utc()

    return EmailAttachmentInfo(
        DetectionMethods=email["detection_methods"],
        FileExtension=attachment["extension"],
        FileName=attachment["file_name"],
        FileSize=attachment["file_size"],
        FileType=attachment["file_type"],
        NetworkMessageId=email["network_message_id"],
        RecipientEmailAddress=recipient.upn,
        RecipientObjectId=recipient.object_id,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SenderDisplayName=email["sender_display_name"],
        SenderFromAddress=email["sender_from_address"],
        SenderObjectId=email["sender_object_id"],
        SHA256=attachment["sha256"],
        SourceSystem="Azure",
        TenantId=world.tenant_id,
        ThreatNames=email["threat_names"],
        ThreatTypes=email["threat_types"],
        TimeGenerated=timestamp,
        Type="EmailAttachmentInfo",
    )
