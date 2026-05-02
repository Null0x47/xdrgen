from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileMaliciousContentInfo(BaseModel):
    DetectionMethods: Optional[str] = Field(None, description="Verdict from the email filtering stack on whether the email contains malware, phishing, or other threats.")
    DocumentID: Optional[str] = Field(None, description="Unique identifier of the file.")
    FileCreationTime: Optional[datetime] = Field(None, description="Timestamp of the file creation.")
    FileName: Optional[str] = Field(None, description="Name of the file that the recorded action was applied to.")
    FileOwnerDisplayName: Optional[str] = Field(None, description="Account recorded as owner of the file.")
    FileOwnerUpn: Optional[str] = Field(None, description="Account recorded as owner of the file")
    FileSize: Optional[int] = Field(None, description="Size of the file in bytes.")
    FolderPath: Optional[str] = Field(None, description="Folder containing the file that the recorded action was applied to.")
    LastModifiedTime: Optional[datetime] = Field(None, description="Date and time the item, or related metadata was last modified.")
    LastModifyingAccountUpn: Optional[str] = Field(None, description="Account that last modified this file.")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event.")
    SHA256: Optional[str] = Field(None, description="SHA-256 of the file that the recorded action was applied to.")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    ThreatNames: Optional[str] = Field(None, description="Detection name for malware or other threats found.")
    ThreatTypes: Optional[str] = Field(None, description="Verdict from the email filtering stack on whether the email contains malware, phishing, or other threats.")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time (UTC) when the record was generated.")
    Type: Optional[str] = Field(None, description="The name of the table")
    Workload: Optional[str] = Field(None, description="Information about the workload from which the URL originated from.")
