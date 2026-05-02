from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceCustomScriptEvents(BaseModel):
    ActionType: Optional[str] = Field(
        None, description="Type of activity that triggered the event."
    )
    DeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in the service."
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name (FQDN) of the device."
    )
    InitiatingProcessAccountDomain: Optional[str] = Field(
        None,
        description="Domain of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountName: Optional[str] = Field(
        None,
        description="User name of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountObjectId: Optional[str] = Field(
        None,
        description="Azure AD object ID of the user account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountSid: Optional[str] = Field(
        None,
        description="Security Identifier (SID) of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountUpn: Optional[str] = Field(
        None,
        description="User principal name (UPN) of the account that ran the process responsible for the event.",
    )
    InitiatingProcessCommandLine: Optional[str] = Field(
        None,
        description="Command line used to run the process that initiated the event.",
    )
    InitiatingProcessCreationTime: Optional[datetime] = Field(
        None,
        description="Date and time when the process that initiated the event was started.",
    )
    InitiatingProcessFileName: Optional[str] = Field(
        None, description="Name of the process that initiated the event."
    )
    InitiatingProcessFileSize: Optional[int] = Field(
        None, description="Size of the process (image file) that initiated the event."
    )
    InitiatingProcessFolderPath: Optional[str] = Field(
        None,
        description="Folder containing the process (image file) that initiated the event.",
    )
    InitiatingProcessId: Optional[int] = Field(
        None, description="Process ID (PID) of the process that initiated the event."
    )
    InitiatingProcessMD5: Optional[str] = Field(
        None,
        description="MD5 hash of the process (image file) that initiated the event.",
    )
    InitiatingProcessParentCreationTime: Optional[datetime] = Field(
        None,
        description="Date and time when the parent of the process responsible for the event was started.",
    )
    InitiatingProcessParentFileName: Optional[str] = Field(
        None,
        description="Name of the parent process that spawned the process responsible for the event.",
    )
    InitiatingProcessParentId: Optional[int] = Field(
        None,
        description="Process ID (PID) of the parent process that spawned the process responsible for the event.",
    )
    InitiatingProcessSHA1: Optional[str] = Field(
        None,
        description="SHA-1 hash of the process (image file) that initiated the event.",
    )
    InitiatingProcessSHA256: Optional[str] = Field(
        None,
        description="SHA-256 hash of the process (image file) that initiated the event. This field is usually not populated - use the SHA1 column when available.",
    )
    InitiatingProcessSignatureStatus: Optional[str] = Field(
        None,
        description="Information about the signature status of the process (image file) that initiated the event.",
    )
    InitiatingProcessSignerType: Optional[str] = Field(
        None,
        description="Type of file signer of the process (image file) that initiated the event.",
    )
    InitiatingProcessVersionInfoCompanyName: Optional[str] = Field(
        None,
        description="Company name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoFileDescription: Optional[str] = Field(
        None,
        description="Description from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoInternalFileName: Optional[str] = Field(
        None,
        description="Internal file name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoOriginalFileName: Optional[str] = Field(
        None,
        description="Original file name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoProductName: Optional[str] = Field(
        None,
        description="Product name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoProductVersion: Optional[str] = Field(
        None,
        description="Product version from the version information of the process (image file) responsible for the event.",
    )
    ReportId: Optional[int] = Field(
        None,
        description="Event identifier based on a repeating counter. To identify unique events, this column must be used in conjunction with the DeviceName and Timestamp columns.",
    )
    RuleLastModificationTime: Optional[datetime] = Field(
        None,
        description="Date and time when the rule that collected the event was last modified.",
    )
    RuleName: Optional[str] = Field(
        None, description="Name of the rule that collected the event"
    )
    ScriptContent: Optional[str] = Field(
        None, description="Content of the executed script."
    )
    ScriptContentSHA256: Optional[str] = Field(
        None, description="SHA256 over the script content."
    )
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(
        None,
        description="Date and time the event was recorded by the MDE agent on the endpoint.",
    )
    Timestamp: Optional[datetime] = Field(
        None, description="Date and time when the record was generated."
    )
    Type: Optional[str] = Field(None, description="The name of the table")
