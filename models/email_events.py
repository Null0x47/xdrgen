from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class EmailEvents(BaseModel):
    AdditionalFields: Optional[Any] = Field(
        None, description="Additional information about the entity or event."
    )
    AttachmentCount: Optional[int] = Field(
        None, description="Number of attachments in the email."
    )
    AuthenticationDetails: Optional[str] = Field(
        None,
        description="List of pass or fail verdicts by email authentication protocols like DMARC, DKIM, SPF or a combination of multiple authentication types (CompAuth).",
    )
    BulkComplaintLevel: Optional[int] = Field(
        None,
        description="Threshold assigned to email from bulk mailers, a high bulk complaint level (BCL) means the email is more likely to generate complaints, and thus more likely to be spam.",
    )
    Cc: Optional[Any] = Field(
        None,
        description="Indicates the addresses which are listed in Cc fields of an email",
    )
    ConfidenceLevel: Optional[str] = Field(
        None,
        description='List of confidence levels of any spam or phishing verdicts. For spam, this column shows the spam confidence level (SCL), indicating if the email was skipped (-1), found to be not spam (0,1), found to be spam with moderate confidence (5,6), or found to be spam with high confidence (9). For phishing, this column displays whether the confidence level is "High" or "Low".',
    )
    Connectors: Optional[str] = Field(
        None,
        description="Custom instructions that define organizational mail flow and how the email was routed.",
    )
    Context: Optional[str] = Field(
        None, description="Configuration context data of the machine"
    )
    DeliveryAction: Optional[str] = Field(
        None, description="Action of the delivered email."
    )
    DeliveryLocation: Optional[str] = Field(
        None,
        description="Location of the delivered email: Inbox/Folder, On-premises/External, Junk, Quarantine, Failed, Dropped, Deleted items.",
    )
    DetectionMethods: Optional[str] = Field(
        None,
        description="Delivery action of the email: Delivered, Junked, Blocked, or Replaced.",
    )
    DistributionList: Optional[str] = Field(
        None,
        description="Name of distribution list that the recipient was a member of and to which the email was sent, if applicable; shows top-level distribution list if nested lists are involved",
    )
    EmailAction: Optional[str] = Field(
        None,
        description="Final action taken on the email based on filter verdict, policies, and user actions: Move message to junk mail folder, Add X-header, Modify subject, Redirect message, Delete message, send to quarantine, No action taken, Bcc message.",
    )
    EmailActionPolicy: Optional[str] = Field(
        None,
        description="Action policy that took effect: Antispam high-confidence, Antispam, Antispam bulk mail, Antispam phishing, Anti-phishing domain impersonation, Anti-phishing user impersonation, Anti-phishing spoof, Anti-phishing graph impersonation, Antimalware Safe Attachments, Enterprise Transport Rules (ETR).",
    )
    EmailActionPolicyGuid: Optional[str] = Field(
        None, description="Unique identifier of the policy that took effect."
    )
    EmailClusterId: Optional[int] = Field(
        None,
        description="Identifier of the email cluster. Emails are clustered (grouped) based on heuristic analysis of their contents.",
    )
    EmailDirection: Optional[str] = Field(
        None, description="Email direction: Inbound, Outbound, Intra-org."
    )
    EmailLanguage: Optional[str] = Field(
        None, description="Detected language of the email content."
    )
    EmailSize: Optional[int] = Field(None, description="Size of the email message.")
    ExchangeTransportRule: Optional[str] = Field(
        None,
        description="Mail flow rules (also known as transport rules) are similar to Inbox rules that are available in Outlook and Outlook on the web. The main difference is mail flow rules take action on messages while they're in transit.",
    )
    ForwardingInformation: Optional[str] = Field(
        None,
        description="A JSON array of forwarding details including the forwarding user and the forwarding type",
    )
    InternetMessageId: Optional[str] = Field(
        None,
        description="Public-facing identifier for the email that is set by the sending email system.",
    )
    IsFirstContact: Optional[bool] = Field(
        None, description="Is this the first contact between sender and reciever."
    )
    LastEventExecutionTime: Optional[datetime] = Field(
        None, description="Date and time (UTC) when the record was updated post merge."
    )
    LatestDeliveryAction: Optional[str] = Field(
        None,
        description="Last known action attempted on an email by the service or by an admin through manual remediation.",
    )
    LatestDeliveryLocation: Optional[str] = Field(
        None, description="Last known location of the email."
    )
    NetworkMessageId: Optional[str] = Field(
        None, description="Unique identifier for the email, generated by Office 365."
    )
    OrgLevelAction: Optional[str] = Field(
        None,
        description="Action taken on the email in response to matches to a policy defined at the organizational level.",
    )
    OrgLevelPolicy: Optional[str] = Field(
        None,
        description="Organizational policy that triggered the action taken on the email.",
    )
    RecipientDomain: Optional[str] = Field(
        None, description="Domain of the recipient of the email."
    )
    RecipientEmailAddress: Optional[str] = Field(
        None,
        description="Recipient email address or email address of the recipient after distribution list expansion.",
    )
    RecipientObjectId: Optional[str] = Field(
        None, description="Email recipient Azure AD identifier."
    )
    ReportId: Optional[str] = Field(
        None, description="Unique identifier for the event."
    )
    SenderDisplayName: Optional[str] = Field(
        None,
        description="Sender email address in the from header, which is visible to email recipients on their email clients.",
    )
    SenderFromAddress: Optional[str] = Field(
        None,
        description="Sender domain in the from header, which is visible to email recipients on their email clients.",
    )
    SenderFromDomain: Optional[str] = Field(
        None,
        description="Verdict from the email filtering stack on whether the email contains malware, phishing, or other threats.",
    )
    SenderIPv4: Optional[str] = Field(
        None,
        description="IPv4 address of the last detected mail server that relayed the message.",
    )
    SenderIPv6: Optional[str] = Field(
        None,
        description="IPv6 address of the last detected mail server that relayed the message.",
    )
    SenderMailFromAddress: Optional[str] = Field(
        None,
        description="Sender email address in the MAIL from header, also known as the envelope sender or the Return-Path address.",
    )
    SenderMailFromDomain: Optional[str] = Field(
        None,
        description="Sender domain in the MAIL from header, also known as the envelope sender or the Return-Path address.",
    )
    SenderObjectId: Optional[str] = Field(
        None,
        description="Sender email address in the from header, which is visible to email recipients on their email clients.",
    )
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    Subject: Optional[str] = Field(None, description="Email subject field.")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    ThreatClassification: Optional[str] = Field(
        None, description="Indicates the threat classification of the mail"
    )
    ThreatNames: Optional[str] = Field(
        None,
        description="Sender email address in the from header, which is visible to email recipients on their email clients.",
    )
    ThreatTypes: Optional[str] = Field(
        None,
        description="Verdict from the email filtering stack on whether the email contains malware, phishing, or other threats.",
    )
    TimeGenerated: Optional[datetime] = Field(
        None, description="Date and time (UTC) when the record was generated."
    )
    To: Optional[Any] = Field(
        None,
        description="Indicates the addresses which are listed in To fields of an email",
    )
    Type: Optional[str] = Field(None, description="The name of the table")
    UrlCount: Optional[int] = Field(
        None, description="Number of embedded URLs in the email."
    )
    UserLevelAction: Optional[str] = Field(
        None,
        description="Action taken on the email in response to matches to a mailbox policy defined by the recipient.",
    )
    UserLevelPolicy: Optional[str] = Field(
        None,
        description="End user mailbox policy that triggered the action taken on the email.",
    )
