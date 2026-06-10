from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class CloudDnsEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the entity or event")
    AwsResourceName: Optional[str] = Field(None, description="Unique identifier specific to Amazon Web Services devices, containing the Amazon resource name")
    AzureResourceId: Optional[str] = Field(None, description="Unique identifier of the Azure resource associated with the process")
    ContainerId: Optional[str] = Field(None, description="The container identifier in Kubernetes or another runtime environment")
    ContainerName: Optional[str] = Field(None, description="Name of the container in Kubernetes or another runtime environment")
    DnsEventSubType: Optional[str] = Field(None, description="Either request or response")
    DnsEventType: Optional[str] = Field(None, description="Type of event associated with DNS operation (for example, query)")
    DnsNetworkDuration: Optional[int] = Field(None, description="The DNS request duration in milliseconds")
    DnsQuery: Optional[str] = Field(None, description="The domain that needs to be resolved")
    DnsQueryTypeName: Optional[str] = Field(None, description="The DNS resource record type name as defined by the Internet Assigned Numbers Authority (IANA)")
    DnsResponseCodeName: Optional[str] = Field(None, description="The DNS response code name as defined by the Internet Assigned Numbers Authority (IANA).")
    GcpFullResourceName: Optional[str] = Field(None, description="Unique identifier specific to Google Cloud Platform devices, containing a combination of zone and ID for GCP")
    ImageName: Optional[str] = Field(None, description="Container image name or ID")
    KubernetesNamespace: Optional[str] = Field(None, description="The Kubernetes namespace name")
    KubernetesPodName: Optional[str] = Field(None, description="The Kubernetes pod name")
    KubernetesResource: Optional[str] = Field(None, description="Unique identifier for the Kubernetes resource that includes the namespace, resource type and name")
    ProcessId: Optional[int] = Field(None, description="Process ID that initiated the DNS query")
    ProcessName: Optional[str] = Field(None, description="The name of the process that initiated the DNS query")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time (UTC) when the record was generated")
    TransactionIdHex: Optional[str] = Field(None, description="The DNS unique hex transaction ID")
    Type: Optional[str] = Field(None, description="The name of the table")
