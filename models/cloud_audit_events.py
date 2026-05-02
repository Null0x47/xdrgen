from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class CloudAuditEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    DataSource: Optional[str] = Field(None, description="Data source for the cloud audit events, can be GCP (for Google Cloud Platform), AWS (for Amazon Web Services), Azure (for Azure Resource Manager), Kubernetes Audit (for Kubernetes), or other cloud platforms")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event, can be: Unknown, Create, Read, Update, Delete, Other")
    OperationName: Optional[str] = Field(None, description="Audit event operation name as it appears in the record, usually includes both resource type and operation")
    ResourceId: Optional[str] = Field(None, description="Unique identifier of the cloud resource accessed")
    IPAddress: Optional[str] = Field(None, description="The client IP address used to access the cloud resource or control plane")
    IsAnonymousProxy: Optional[bool] = Field(None, description="Indicates whether the IP address belongs to a known anonymous proxy (1) or no (0)")
    CountryCode: Optional[str] = Field(None, description="Two-letter code indicating the country where the client IP address is geolocated")
    City: Optional[str] = Field(None, description="City where the client IP address is geolocated")
    Isp: Optional[str] = Field(None, description="Internet service provider (ISP) associated with the IP address")
    UserAgent: Optional[str] = Field(None, description="User agent information from the web browser or other client application")
    RawEventData: Optional[Any] = Field(None, description="Full raw event information from the data source in JSON format")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the audit event")
