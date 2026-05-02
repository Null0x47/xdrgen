from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBehaviorInfo(BaseModel):
    AccountObjectId: Optional[str] = Field(
        None, description="Unique identifier for the account in Azure AD."
    )
    AccountUpn: Optional[str] = Field(
        None, description="User principal name (UPN) of the account."
    )
    ActionType: Optional[str] = Field(
        None,
        description="Type of activity that triggered the event. Associated with specific MITRE ATT&CK techniques.",
    )
    AdditionalFields: Optional[str] = Field(
        None, description="Additional information about the entity or event."
    )
    AttackTechniques: Optional[str] = Field(
        None,
        description="MITRE ATT&CK techniques associated with the activity that triggered the alert. Defined by the MITRE ATT&CK Matrix for Enterprise.",
    )
    BehaviorId: Optional[str] = Field(
        None, description="Unique identifier for the behavior."
    )
    Categories: Optional[str] = Field(
        None,
        description="Types of threat indicator or breach activity identified by the alert. Defined by the MITRE ATT&CK Matrix for Enterprise.",
    )
    DataSources: Optional[str] = Field(
        None,
        description="Products or services that provided information for the behavior.",
    )
    Description: Optional[str] = Field(None, description="Description of the behavior.")
    DetectionSource: Optional[str] = Field(
        None,
        description="Detection technology or sensor that identified the notable component or activity.",
    )
    DeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in the service."
    )
    EndTime: Optional[datetime] = Field(
        None, description="Date and time of the last activity related to the behavior."
    )
    ServiceSource: Optional[str] = Field(
        None, description="Product or service that provided the alert information."
    )
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    StartTime: Optional[datetime] = Field(
        None, description="Date and time of the first activity related to the behavior."
    )
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(
        None, description="Date and time when the record was generated."
    )
    Type: Optional[str] = Field(None, description="The name of the table")
