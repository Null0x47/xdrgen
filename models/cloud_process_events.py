from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CloudProcessEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    AzureResourceId: Optional[str] = Field(None, description="Unique identifier of the Azure resource associated with the process")
    AwsResourceName: Optional[str] = Field(None, description="Unique identifier specific to Amazon Web Services devices, containing the Amazon resource name")
    GcpFullResourceName: Optional[str] = Field(None, description="Unique identifier specific to Google Cloud Platform devices, containing a combination of zone and ID for GCP")
    ContainerImageName: Optional[str] = Field(None, description="The container image name or ID, if it exists")
    KubernetesNamespace: Optional[str] = Field(None, description="The Kubernetes namespace name")
    KubernetesPodName: Optional[str] = Field(None, description="The Kubernetes pod name")
    KubernetesResource: Optional[str] = Field(None, description="Identifier value that includes namespace, resource type and name")
    ContainerName: Optional[str] = Field(None, description="Name of the container in Kubernetes or another runtime environment")
    ContainerId: Optional[str] = Field(None, description="The container identifier in Kubernetes or another runtime environment")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event. See the in-portal schema reference for details.")
    FileName: Optional[str] = Field(None, description="Name of the file that the recorded action was applied to")
    FolderPath: Optional[str] = Field(None, description="Folder containing the file that the recorded action was applied to")
    ProcessId: Optional[int] = Field(None, description="Process ID (PID) of the newly created process")
    ProcessName: Optional[str] = Field(None, description="The name of the process")
    ParentProcessName: Optional[str] = Field(None, description="The name of the parent process")
    ParentProcessId: Optional[str] = Field(None, description="The process ID (PID) of the parent process")
    ProcessCommandLine: Optional[str] = Field(None, description="Command line used to create the new process")
    ProcessCreationTime: Optional[datetime] = Field(None, description="Date and time the process was created")
    ProcessCurrentWorkingDirectory: Optional[str] = Field(None, description="Current working directory of the running process")
    AccountName: Optional[str] = Field(None, description="User name of the account")
    LogonId: Optional[int] = Field(None, description="Identifier for a logon session. This identifier is unique on the same pod or container between restarts.")
    InitiatingProcessId: Optional[str] = Field(None, description="Process ID (PID) of the process that initiated the event")
    AdditionalFields: Optional[str] = Field(None, description="Additional information about the event in JSON array format")
