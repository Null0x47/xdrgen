from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntraIdSignInEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(
        None, description="Date and time when the record was generated"
    )
    Application: Optional[str] = Field(
        None, description="Application that performed the recorded action"
    )
    ApplicationId: Optional[str] = Field(
        None, description="Unique identifier for the application"
    )
    LogonType: Optional[str] = Field(
        None,
        description="Type of logon session, specifically interactive, remote interactive (RDP), network, batch, and service",
    )
    ErrorCode: Optional[int] = Field(
        None,
        description="Contains the error code if a sign-in error occurs. To find a description of a specific error code, visithttps://aka.ms/AADsigninsErrorCodes.",
    )
    CorrelationId: Optional[str] = Field(
        None, description="Identifier of the sign-in event"
    )
    SessionId: Optional[str] = Field(
        None,
        description="Unique number assigned to a user by a website's server for the duration of the visit or session",
    )
    AccountDisplayName: Optional[str] = Field(
        None,
        description="Name displayed in the address book entry for the account user. This is usually a combination of the given name, middle initial, and surname of the user.",
    )
    AccountObjectId: Optional[str] = Field(
        None, description="Unique identifier for the account in Microsoft Entra ID"
    )
    AccountUpn: Optional[str] = Field(
        None, description="User principal name (UPN) of the account"
    )
    IsConfidentialClient: Optional[bool] = Field(
        None,
        description="Indicates if the sign in was done via confidential client applications",
    )
    IsExternalUser: Optional[int] = Field(
        None,
        description="Indicates if the user that signed in is external. Possible values: -1 (not set), 0 (not external), 1 (external).",
    )
    IsGuestUser: Optional[bool] = Field(
        None,
        description="Indicates if the sign in was done via confidential client applications",
    )
    AlternateSignInName: Optional[str] = Field(
        None,
        description="On-premises user principal name (UPN) of the user signing in to Microsoft Entra ID",
    )
    LastPasswordChangeTimestamp: Optional[datetime] = Field(
        None,
        description="Date and time when the user that signed in last changed their password",
    )
    ResourceDisplayName: Optional[str] = Field(
        None,
        description="Display name of the resource accessed. The display name can contain any character.",
    )
    ResourceId: Optional[str] = Field(
        None, description="Unique identifier of the resource accessed"
    )
    ResourceTenantId: Optional[str] = Field(
        None, description="Unique identifier of the tenant of the resource accessed"
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name (FQDN) of the device"
    )
    EntraIdDeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in Microsoft Entra ID"
    )
    OSPlatform: Optional[str] = Field(
        None,
        description="Platform of the operating system running on the device. Indicates specific operating systems, including variations within the same family, such as Windows 11, Windows 10, and Windows 7.",
    )
    DeviceTrustType: Optional[str] = Field(
        None,
        description="Indicates the trust type of the device that signed in. For managed device scenarios only. Possible values are Workplace, AzureAd, and ServerAd.",
    )
    IsManaged: Optional[int] = Field(
        None,
        description="Indicates whether the device that initiated the sign-in is a managed device (1) or not a managed device (0)",
    )
    IsCompliant: Optional[int] = Field(
        None,
        description="Indicates whether the device that initiated the sign-in is compliant (1) or non-compliant (0)",
    )
    AuthenticationProcessingDetails: Optional[str] = Field(
        None, description="Details about the authentication processor"
    )
    AuthenticationRequirement: Optional[str] = Field(
        None,
        description="Type of authentication required for the sign-in. Possible values: multiFactorAuthentication (MFA was required) and singleFactorAuthentication (no MFA was required).",
    )
    TokenIssuerType: Optional[int] = Field(
        None,
        description="Indicates if the token issuer is Microsoft Entra ID (0) or Active Directory Federation Services (1)",
    )
    RiskLevelAggregated: Optional[int] = Field(
        None,
        description="Aggregated risk level during sign-in. Possible values: 0 (aggregated risk level not set), 1 (none), 10 (low), 50 (medium), or 100 (high).",
    )
    RiskDetails: Optional[int] = Field(
        None, description="Details about the risky state of the user that signed in"
    )
    RiskState: Optional[int] = Field(
        None,
        description="Indicates risky user state. Possible values: 0 (none), 1 (confirmed safe), 2 (remediated), 3 (dismissed), 4 (at risk), or 5 (confirmed compromised).",
    )
    UserAgent: Optional[str] = Field(
        None,
        description="User agent information from the web browser or other client application",
    )
    ClientAppUsed: Optional[str] = Field(
        None, description="Indicates the client app used"
    )
    Browser: Optional[str] = Field(
        None, description="Details about the version of the browser used to sign in"
    )
    ConditionalAccessPolicies: Optional[str] = Field(
        None,
        description="Details of the conditional access policies applied to the sign-in event",
    )
    ConditionalAccessStatus: Optional[int] = Field(
        None,
        description="Status of the conditional access policies applied to the sign-in. Possible values are 0 (policies applied), 1 (attempt to apply policies failed), or 2 (policies not applied).",
    )
    IPAddress: Optional[str] = Field(
        None, description="IP address assigned to the device during communication"
    )
    Country: Optional[str] = Field(
        None,
        description="Two-letter code indicating the country/region where the client IP address is geolocated",
    )
    State: Optional[str] = Field(
        None, description="State where the sign-in occurred, if available"
    )
    City: Optional[str] = Field(
        None, description="City where the account user is located"
    )
    Latitude: Optional[str] = Field(
        None, description="The north to south coordinates of the sign-in location"
    )
    Longitude: Optional[str] = Field(
        None, description="The east to west coordinates of the sign-in location"
    )
    NetworkLocationDetails: Optional[str] = Field(
        None,
        description="Network location details of the authentication processor of the sign-in event",
    )
    RequestId: Optional[str] = Field(
        None, description="Unique identifier of the request"
    )
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    EndpointCall: Optional[str] = Field(
        None,
        description="Information about the Microsoft Entra ID endpoint that the request was sent to and the type of request sent during sign in.",
    )
