from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class CloudDnsEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event")
    AzureResourceId: Optional[str] = Field(None, description="Unique identifier of the Azure resource associated with the process")
    AwsResourceName: Optional[str] = Field(None, description="Unique identifier specific to Amazon Web Services devices, containing the Amazon resource name")
    GcpFullResourceName: Optional[str] = Field(None, description="Unique identifier specific to Google Cloud Platform devices, containing a combination of zone and ID for GCP")
    KubernetesResource: Optional[str] = Field(None, description="Unique identifier for the Kubernetes resource that includes the namespace, resource type and name")
    KubernetesNamespace: Optional[str] = Field(None, description="The Kubernetes namespace name")
    KubernetesPodName: Optional[str] = Field(None, description="The Kubernetes pod name")
    ContainerName: Optional[str] = Field(None, description="Name of the container in Kubernetes or another runtime environment")
    ContainerId: Optional[str] = Field(None, description="The container identifier in Kubernetes or another runtime environment")
    ImageName: Optional[str] = Field(None, description="Container image name or ID")
    ProcessName: Optional[str] = Field(None, description="The name of the process that initiated the DNS query")
    ProcessId: Optional[int] = Field(None, description="Process ID that initiated the DNS query")
    DnsEventType: Optional[str] = Field(None, description="Type of event associated with DNS operation (for example, query)")
    DnsEventSubType: Optional[str] = Field(None, description="Either request or response")
    DnsQuery: Optional[str] = Field(None, description="The domain that needs to be resolved")
    DnsQueryTypeName: Optional[str] = Field(None, description="The DNS resource record type name as defined by the Internet Assigned Numbers Authority (IANA)")
    DnsResponseCodeName: Optional[str] = Field(None, description="The DNS response code name as defined by the Internet Assigned Numbers Authority (IANA).")
    DnsNetworkDuration: Optional[int] = Field(None, description="The DNS request duration in milliseconds")
    TransactionIdHex: Optional[str] = Field(None, description="The DNS unique hex transaction ID")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the entity or event")
