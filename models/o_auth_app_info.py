from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class OAuthAppInfo(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    AddedOnTime: Optional[datetime] = Field(None, description="Date and time when the application was registered")
    AppName: Optional[str] = Field(None, description="The application's display name as exposed by the associated service principal")
    AppOrigin: Optional[str] = Field(None, description="Specifies whether the app is internal to the organization or registered in an external tenant")
    AppOwnerTenantId: Optional[str] = Field(None, description="Specifies the ID of the tenant where the app was registered")
    AppStatus: Optional[str] = Field(None, description="Status of the app; can be: Enabled, DisabledByMicrosoft, DisabledByAppGovernancePolicy, DisabledByUser, Deleted")
    ConsentedUsersCount: Optional[int] = Field(None, description="Count of users who have consented to the app")
    IsAdminConsented: Optional[bool] = Field(None, description="Value is True if a user has provided admin consent to the app on behalf of all the users in the org, otherwise False")
    LastModifiedTime: Optional[datetime] = Field(None, description="Timestamp when the app was last modified")
    LastUsedTime: Optional[datetime] = Field(None, description="Date and time when the app last signed in")
    OAuthAppId: Optional[str] = Field(None, description="The unique identifier for the app as assigned by Microsoft Entra ID")
    Permissions: Optional[Any] = Field(None, description="Contains an array of permission objects")
    PrivilegeLevel: Optional[str] = Field(None, description="The privilege level of the app based on the highest classified permission granted to the app")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the record")
    ServicePrincipalId: Optional[str] = Field(None, description="The unique identifier for the service principal instance of the application in the tenant")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time (UTC) when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
    VerifiedPublisher: Optional[Any] = Field(None, description="Specifies details about the verified publisher of the application which this service principal represents")
