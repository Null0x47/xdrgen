from __future__ import annotations

import random

from models import EmailEvents
from generators.base import register
from generators.common import now_utc
from generators.email_pool import pool_for
from world import World


@register("EmailEvents")
def generate(world: World) -> EmailEvents:
    email = pool_for(world).pick()
    recipient = email["recipient"]
    timestamp = now_utc()

    threat_types = email["threat_types"]
    delivery_action = email["delivery_action"]

    # Tenant-wide blocks → OrgLevelPolicy; per-user → mailbox rules.
    if email["email_action_policy"]:
        org_level_policy = email["email_action_policy"]
        org_level_action = email["email_action"]
    else:
        org_level_policy = None
        org_level_action = None

    return EmailEvents(
        AdditionalFields={},
        AttachmentCount=len(email["attachments"]),
        AuthenticationDetails=email["authentication_details"],
        BulkComplaintLevel=email["bulk_complaint_level"],
        Cc=[],
        ConfidenceLevel=email["confidence_level"],
        Connectors=None,
        Context=None,
        DeliveryAction=delivery_action,
        DeliveryLocation=email["delivery_location"],
        DetectionMethods=email["detection_methods"],
        DistributionList=None,
        EmailAction=email["email_action"],
        EmailActionPolicy=email["email_action_policy"],
        EmailActionPolicyGuid=email["email_action_policy_guid"],
        EmailClusterId=random.randint(10**11, 10**12 - 1),
        EmailDirection=email["direction"],
        EmailLanguage=email["language"],
        EmailSize=email["email_size"],
        ExchangeTransportRule=None,
        ForwardingInformation=None,
        InternetMessageId=email["internet_message_id"],
        IsFirstContact=email["is_first_contact"],
        LastEventExecutionTime=timestamp,
        LatestDeliveryAction=delivery_action,
        LatestDeliveryLocation=email["delivery_location"],
        NetworkMessageId=email["network_message_id"],
        OrgLevelAction=org_level_action,
        OrgLevelPolicy=org_level_policy,
        RecipientDomain=recipient.upn.split("@", 1)[-1],
        RecipientEmailAddress=recipient.upn,
        RecipientObjectId=recipient.object_id,
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SenderDisplayName=email["sender_display_name"],
        SenderFromAddress=email["sender_from_address"],
        SenderFromDomain=email["sender_from_domain"],
        SenderIPv4=email["sender_ipv4"],
        SenderIPv6=email["sender_ipv6"],
        SenderMailFromAddress=email["sender_mail_from_address"],
        SenderMailFromDomain=email["sender_mail_from_domain"],
        SenderObjectId=email["sender_object_id"],
        SourceSystem="Azure",
        Subject=email["subject"],
        TenantId=world.tenant_id,
        ThreatClassification=email["threat_classification"],
        ThreatNames=email["threat_names"],
        ThreatTypes=threat_types,
        TimeGenerated=timestamp,
        To=[recipient.upn],
        Type="EmailEvents",
        UrlCount=len(email["urls"]),
        UserLevelAction=None,
        UserLevelPolicy=None,
    )
