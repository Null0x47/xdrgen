from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class IdentityLogonEvents(BaseModel):
    AccountDisplayName: Optional[str] = Field(None, description="Name of the account user displayed in the address book")
    AccountDomain: Optional[str] = Field(None, description="Domain of the account")
    AccountName: Optional[str] = Field(None, description="User name of the account")
    AccountObjectId: Optional[str] = Field(None, description="Unique identifier for the account in Azure AD")
    AccountSid: Optional[str] = Field(None, description="Security Identifier (SID) of the account")
    AccountUpn: Optional[str] = Field(None, description="User principal name (UPN) of the account")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the entity or event")
    Application: Optional[str] = Field(None, description="Application that performed the recorded action")
    DestinationDeviceName: Optional[str] = Field(None, description="Name of the device running the server application that processed the recorded action")
    DestinationIPAddress: Optional[str] = Field(None, description="IP address of the device running the server application that processed the recorded action")
    DestinationPort: Optional[str] = Field(None, description="Destination port of related network communications")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device")
    DeviceType: Optional[str] = Field(None, description="Type of device")
    FailureReason: Optional[str] = Field(None, description="Information explaining why the recorded action failed")
    IPAddress: Optional[str] = Field(None, description="IP address assigned to the endpoint and used during related network communications")
    ISP: Optional[str] = Field(None, description="Internet service provider (ISP) associated with the endpoint IP address")
    LastSeenForUser: Optional[Any] = Field(None, description="Number of days since each statistical feature for the user was last seen")
    Location: Optional[str] = Field(None, description="City, country, or other geographic location associated with the event")
    LogonType: Optional[str] = Field(None, description="Type of logon session")
    OSPlatform: Optional[str] = Field(None, description="Platform of the operating system running on the machine")
    Port: Optional[str] = Field(None, description="TCP port used during communication")
    Protocol: Optional[str] = Field(None, description="Network protocol used")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TargetAccountDisplayName: Optional[str] = Field(None, description="Display name of the account that the recorded action was applied to")
    TargetDeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device that the recorded action was applied to")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time (UTC) when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
    UncommonForUser: Optional[Any] = Field(None, description="List of features observed to be statistically uncommon for the user that performed the activity")
