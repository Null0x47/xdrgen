from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CloudPolicyEnforcementEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    DataSource: Optional[str] = Field(None, description="Data source of the cloud events; possible values: Google Kubernetes Engine, Elastic Kubernetes Service, or Azure Kubernetes Service")
    SubscriptionId: Optional[str] = Field(None, description="Unique identifier assigned to the Azure subscription")
    ActionType: Optional[str] = Field(None, description="Type of activity that resulted from the policy enforcement operation; possible values: Audit, Deny, or Allow")
    AzureResourceId: Optional[str] = Field(None, description="Unique identifier of the Azure resource associated with the event")
    AwsResourceName: Optional[str] = Field(None, description="Unique identifier specific to Amazon Web Services devices, containing the Amazon resource name")
    GcpFullResourceName: Optional[str] = Field(None, description="Unique identifier specific to Google Cloud Platform devices, containing a combination of zone and ID for GCP")
    Region: Optional[str] = Field(None, description="The region associated with the Kubernetes cluster")
    ResourceKind: Optional[str] = Field(None, description="Type or kind of Kubernetes resource created or managed (for example, pod or deployment)")
    ResourceName: Optional[str] = Field(None, description="Name of the Kubernetes resource")
    KubernetesNamespace: Optional[str] = Field(None, description="The Kubernetes namespace name")
    Reason: Optional[str] = Field(None, description="Information explaining the action result")
    AdditionalFields: Optional[str] = Field(None, description="Additional information about the entity or event")
