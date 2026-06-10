from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class CloudAuditEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event, can be: Unknown, Create, Read, Update, Delete, Other")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the audit event")
    City: Optional[str] = Field(None, description="City where the client IP address is geolocated")
    CloudResourceId: Optional[str] = Field(None, description="Unique identifier of the cloud resource accessed")
    CountryCode: Optional[str] = Field(None, description="Two-letter code indicating the country where the client IP address is geolocated")
    DataSource: Optional[str] = Field(None, description="Data source for the cloud audit events, can be GCP (for Google Cloud Platform), AWS (for Amazon Web Services), Azure (for Azure Resource Manager), Kubernetes Audit (for Kubernetes), or other cloud platforms")
    IPAddress: Optional[str] = Field(None, description="The client IP address used to access the cloud resource or control plane")
    IsAnonymousProxy: Optional[bool] = Field(None, description="Indicates whether the IP address belongs to a known anonymous proxy (1) or no (0)")
    Isp: Optional[str] = Field(None, description="Internet service provider (ISP) associated with the IP address")
    OperationName: Optional[str] = Field(None, description="Audit event operation name as it appears in the record, usually includes both resource type and operation")
    RawEventData: Optional[Any] = Field(None, description="Full raw event information from the data source in JSON format")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time (UTC) when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
    UserAgent: Optional[str] = Field(None, description="User agent information from the web browser or other client application")
