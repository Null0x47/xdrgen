from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSoftwareVulnerabilities(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    CveId: Optional[str] = Field(None, description="Unique identifier assigned to the security vulnerability under the Common Vulnerabilities and Exposures (CVE) system")
    CveTags: Optional[Any] = Field(None, description="Array of tags relevant to the CVE; example: ZeroDay, NoSecurityUpdate")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device")
    OSArchitecture: Optional[str] = Field(None, description="Architecture of the operating system running on the machine")
    OSPlatform: Optional[str] = Field(None, description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 10 and Windows 7")
    OSVersion: Optional[str] = Field(None, description="Version of the operating system running on the machine")
    RecommendedSecurityUpdate: Optional[str] = Field(None, description="Name or description of the security update provided by the software vendor to address the vulnerability")
    RecommendedSecurityUpdateId: Optional[str] = Field(None, description="Identifier of the applicable security updates or identifier for the corresponding guidance or knowledge base (KB) articles")
    SoftwareName: Optional[str] = Field(None, description="Name of the software product")
    SoftwareVendor: Optional[str] = Field(None, description="Name of the software vendor")
    SoftwareVersion: Optional[str] = Field(None, description="Version number of the software product")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
    VulnerabilitySeverityLevel: Optional[str] = Field(None, description="Severity level assigned to the security vulnerability based on the CVSS score and dynamic factors influenced by the threat landscape")
