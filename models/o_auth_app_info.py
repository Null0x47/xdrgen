from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class OAuthAppInfo(BaseModel):
    ReportId: Optional[str] = Field(None, description="Unique identifier for the record")
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was created")
    OAuthAppId: Optional[str] = Field(None, description="The unique  identifier for the app as assigned by Microsoft Entra ID")
    ServicePrincipalId: Optional[str] = Field(None, description="The unique identifier for the service principal instance of the application in the tenant")
    AppName: Optional[str] = Field(None, description="The application's display name as exposed by the associated service principal")
    AddedOnTime: Optional[datetime] = Field(None, description="Date and time when the application was registered")
    LastModifiedTime: Optional[datetime] = Field(None, description="Timestamp when the app was last modified")
    AppStatus: Optional[str] = Field(None, description="Status of the app; can be: Enabled, DisabledByMicrosoft, DisabledByAppGovernancePolicy, DisabledByUser, Deleted (information for apps with Deleted status is only available for 30 days since the app was deleted)")
    VerifiedPublisher: Optional[Any] = Field(None, description="Specifies details about the verified publisher of the application which this service principal represents. It includes information such as: DisplayName, VerifiedPublisherId, AddedDateTime")
    PrivilegeLevel: Optional[str] = Field(None, description="The privilege level of the app based on the highest classified permission granted to the app")
    Permissions: Optional[Any] = Field(None, description="Contains an array of permission objects; each permission object includes PermissionName, TargetAppId, TargetAppDisplayName, PermissionType, PrivilegeLevel, UsageStatus")
    ConsentedUsersCount: Optional[int] = Field(None, description="Count of users who have consented to the app; this information is only available when the app isn't admin consented")
    IsAdminConsented: Optional[bool] = Field(None, description="Value is True if a user has provided admin consent to the app on behalf of all the users in the org, otherwise the value is False")
    AppOrigin: Optional[str] = Field(None, description="Specifies whether the app is internal to the organization or registered in an external tenant")
    LastUsedTime: Optional[datetime] = Field(None, description="Date and time when the app last signed in. Tracking of this data goes back to June, 2022")
    AppOwnerTenantId: Optional[str] = Field(None, description="Specifies the ID of the tenant where the app was registered")
