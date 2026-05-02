from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DataSecurityEvents(BaseModel):
    ApplicationNames: Optional[str] = Field(
        None, description="List of application names used or related to the event"
    )
    DeviceId: Optional[str] = Field(
        None,
        description="Unique identifier for the device in Microsoft Defender for Endpoint",
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name(FQDN) of the device"
    )
    AadDeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in Microsoft Entra ID"
    )
    IsManagedDevice: Optional[bool] = Field(
        None,
        description="Indicates if the device is managed by the organization (True) or not (False)",
    )
    DlpPolicyMatchInfo: Optional[str] = Field(
        None,
        description="Information around the list of data loss prevention (DLP) policies matching this event",
    )
    DlpPolicyEnforcementMode: Optional[int] = Field(
        None,
        description="Indicates the Data Loss Prevention policy that was enforced; value can be: 0 (None), 1 (Audit), 2 (Warn), 3 (Warn and bypass), 4 (Block), 5 (Allow)",
    )
    DlpPolicyRuleMatchInfo: Optional[Any] = Field(
        None,
        description="Details of the data loss prevention (DLP)  rules that matched with this event; in JSON array format",
    )
    FileRenameInfo: Optional[str] = Field(
        None,
        description="Details of the file (file name and extension) before this event",
    )
    PhysicalAccessPointId: Optional[str] = Field(
        None, description="Unique identifier for the physical access point"
    )
    PhysicalAccessPointName: Optional[str] = Field(
        None, description="Name of the physical access point"
    )
    PhysicalAccessStatus: Optional[str] = Field(
        None, description="Status of physical access, whether it succeeded or failed"
    )
    PhysicalAssetTag: Optional[str] = Field(
        None,
        description="Tag assigned to the asset as configured in Microsoft Insider Risk Management global settings",
    )
    RemovableMediaManufacturer: Optional[str] = Field(
        None, description="Manufacturer name of the removable device"
    )
    RemovableMediaModel: Optional[str] = Field(
        None, description="Model name of the removable device"
    )
    RemovableMediaSerialNumber: Optional[str] = Field(
        None, description="Serial number of the removable device"
    )
    TeamsChannelName: Optional[str] = Field(
        None, description="Name of the Teams channel"
    )
    TeamsChannelType: Optional[str] = Field(
        None, description="Type of the Teams channel"
    )
    TeamsTeamName: Optional[str] = Field(None, description="Name of the Teams team")
    UserAlternateEmails: Optional[str] = Field(
        None, description="Alternate emails or aliases of the user"
    )
    AccountUpn: Optional[str] = Field(
        None, description="User principal name (UPN) of the account"
    )
    AccountObjectId: Optional[str] = Field(
        None, description="Unique identifier for the account in Microsoft Entra ID"
    )
    Department: Optional[str] = Field(
        None, description="Name of the department that the account user belongs to"
    )
    SourceCodeInfo: Optional[str] = Field(
        None, description="Details of the source code repository involved in the event"
    )
    CcPolicyMatchInfo: Optional[Any] = Field(
        None,
        description="Details of the Communications Compliance policy matches for this event; in JSON array format",
    )
    IPAddress: Optional[str] = Field(
        None,
        description="IP addresses of the clients on which the activity was performed; can contain multiple IPs if related to Microsoft Defender for Cloud Apps alerts",
    )
    Timestamp: Optional[datetime] = Field(
        None, description="Date and time when the event was recorded"
    )
    DeviceSourceLocationType: Optional[int] = Field(
        None,
        description="Indicates the type of location where the endpoint signals originated from; values can be: 0 (Unknown), 1 (Local), 2 (Remote), 3 (Removable), 4 (Cloud), 5 (File share)",
    )
    DeviceDestinationLocationType: Optional[int] = Field(
        None,
        description="Indicates the type of location where the endpoint signals connected to; values can be: 0 (Unknown), 1 (Local), 2 (Remote), 3 (Removable), 4 (Cloud), 5 (File share)",
    )
    IrmPolicyMatchInfo: Optional[Any] = Field(
        None,
        description="Details of Insider Risk Management policy matches for the content involved in the event; in JSON array format",
    )
    UnallowedUrlDomains: Optional[str] = Field(
        None,
        description="Websites or service URLs involved in this event that is configured as Unallowed in Insider Risk Management global settings",
    )
    ExternalUrlDomains: Optional[str] = Field(
        None,
        description="Websites or service URLs involved in this event that is classified as External in Insider Risk Management global settings",
    )
    UrlDomainInfo: Optional[str] = Field(
        None,
        description="Details about the websites or service URLs involved in the event",
    )
    SourceUrlDomain: Optional[str] = Field(
        None, description="Domain where the device and email signals originated"
    )
    TargetUrlDomain: Optional[str] = Field(
        None,
        description="Domain where the content was shared with or the user has browsed to",
    )
    EmailAttachmentCount: Optional[int] = Field(
        None, description="Number of email attachments"
    )
    EmailAttachmentInfo: Optional[Any] = Field(
        None, description="Details of email attachments; in JSON array format"
    )
    InternetMessageId: Optional[str] = Field(
        None,
        description="Public-facing identifier for the email or Teams message that is set by the sending email system",
    )
    NetworkMessageId: Optional[str] = Field(
        None, description="Unique identifier for the email, generated by Microsoft 365"
    )
    EmailSubject: Optional[str] = Field(None, description="Subject of the email")
    ObjectId: Optional[str] = Field(
        None,
        description="Unique identifier of the object that the recorded action was applied to, in case of files, it includes the extension",
    )
    ObjectName: Optional[str] = Field(
        None,
        description="Name of the object that the recorded action was applied to, in case of files, it includes the extension",
    )
    ObjectType: Optional[str] = Field(
        None,
        description="Type of object, such as a file or a folder, that the recorded action was applied to",
    )
    ObjectSize: Optional[int] = Field(None, description="Size of the object in bytes")
    IsHidden: Optional[bool] = Field(
        None,
        description="Indicates whether the user has marked the content as hidden (True) or not (False)",
    )
    ActivityId: Optional[str] = Field(
        None, description="Unique identifier of the activity log"
    )
    ActionType: Optional[str] = Field(
        None, description="Type of activity that triggered the event"
    )
    SensitiveInfoTypeInfo: Optional[Any] = Field(
        None,
        description="Details of Data Loss Prevention sensitive info types detected in the impacted asset",
    )
    SensitivityLabelId: Optional[str] = Field(
        None,
        description="The current Microsoft Information Protection sensitivity label ID associated with the item",
    )
    SharepointSiteSensitivityLabelIds: Optional[str] = Field(
        None,
        description="The current Microsoft Information Protection sensitivity label ID assigned to the parent site of the item related to SharePoint activities",
    )
    PreviousSensitivityLabelId: Optional[str] = Field(
        None,
        description="The previous Microsoft Information Protection sensitivity label ID associated with the item in case of activities where the sensitivity label was changed",
    )
    Operation: Optional[str] = Field(None, description="Name of the admin activity")
    RecipientEmailAddress: Optional[str] = Field(
        None,
        description="Email address of the recipient, or email address of the recipient after distribution list expansion",
    )
    SiteUrl: Optional[str] = Field(
        None,
        description="The URL of the site where the file or folder accessed by the user is located",
    )
    SourceRelativeUrl: Optional[str] = Field(
        None,
        description="The URL of the folder that contains the file accessed by the user",
    )
    TargetFilePath: Optional[str] = Field(
        None, description="Target file path of endpoint activities"
    )
    PrinterName: Optional[str] = Field(
        None, description="List of printers involved in the behavior"
    )
    Workload: Optional[str] = Field(
        None, description="The Microsoft 365 service where the event occurred"
    )
    IrmActionCategory: Optional[str] = Field(
        None,
        description="A unique enumeration value indicating the activity category in Microsoft Purview Insider Risk Management",
    )
    SequenceCorrelationId: Optional[str] = Field(
        None, description="Details of the sequence activity"
    )
    CloudAppAlertId: Optional[str] = Field(
        None,
        description="Unique identifier for the alert in Microsoft Defender for Cloud Apps",
    )
