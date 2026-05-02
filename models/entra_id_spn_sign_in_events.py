from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntraIdSpnSignInEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Application: Optional[str] = Field(None, description="Application that performed the recorded action")
    ApplicationId: Optional[str] = Field(None, description="Unique identifier for the application")
    IsManagedIdentity: Optional[bool] = Field(None, description="Indicates whether the sign-in was initiated by a managed identity")
    ErrorCode: Optional[int] = Field(None, description="Contains the error code if a sign-in error occurs. To find a description of a specific error code, visithttps://aka.ms/AADsigninsErrorCodes.")
    CorrelationId: Optional[str] = Field(None, description="Unique identifier of the sign-in event")
    ServicePrincipalName: Optional[str] = Field(None, description="Name of the service principal that initiated the sign-in")
    ServicePrincipalId: Optional[str] = Field(None, description="Unique identifier of the service principal that initiated the sign-in")
    ResourceDisplayName: Optional[str] = Field(None, description="Display name of the resource accessed. The display name can contain any character.")
    ResourceId: Optional[str] = Field(None, description="Unique identifier of the resource accessed")
    ResourceTenantId: Optional[str] = Field(None, description="Unique identifier of the tenant of the resource accessed")
    IPAddress: Optional[str] = Field(None, description="IP address assigned to the endpoint and used during related network communications")
    Country: Optional[str] = Field(None, description="Two-letter code indicating the country/region where the client IP address is geolocated")
    State: Optional[str] = Field(None, description="State where the sign-in occurred, if available")
    City: Optional[str] = Field(None, description="City where the account user is located")
    Latitude: Optional[str] = Field(None, description="The north to south coordinates of the sign-in location")
    Longitude: Optional[str] = Field(None, description="The east to west coordinates of the sign-in location")
    RequestId: Optional[str] = Field(None, description="Unique identifier of the request")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
