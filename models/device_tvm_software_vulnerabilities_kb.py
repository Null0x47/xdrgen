from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSoftwareVulnerabilitiesKB(BaseModel):
    AffectedSoftware: Optional[Any] = Field(None, description="List of all software products affected by the vulnerability.")
    CveId: Optional[str] = Field(None, description="Unique identifier assigned to the security vulnerability under the Common Vulnerabilities and Exposures (CVE) system.")
    CvssScore: Optional[float] = Field(None, description="Severity score assigned to the security vulnerability under the Common Vulnerability Scoring System (CVSS).")
    IsExploitAvailable: Optional[bool] = Field(None, description="Indicates whether exploit code for the vulnerability is publicly available.")
    LastModifiedTime: Optional[datetime] = Field(None, description="Date and time the item or related metadata was last modified.")
    PublishedDate: Optional[datetime] = Field(None, description="Date vulnerability was disclosed to the public.")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time when the record was generated.")
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
    VulnerabilityDescription: Optional[str] = Field(None, description="Description of the vulnerability and associated risks.")
    VulnerabilitySeverityLevel: Optional[str] = Field(None, description="Severity level assigned to the security vulnerability based on the CVSS score and dynamic factors influenced by the threat landscape.")
