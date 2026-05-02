from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSecureConfigurationAssessment(BaseModel):
    ConfigurationCategory: Optional[str] = Field(None, description="Category or grouping to which the configuration belongs")
    ConfigurationId: Optional[str] = Field(None, description="Unique identifier for a specific configuration")
    ConfigurationImpact: Optional[float] = Field(None, description="Rated impact of the configuration to the overall configuration score (1-10)")
    ConfigurationSubcategory: Optional[str] = Field(None, description="Subcategory or subgrouping to which the configuration belongs. In many cases, this describes specific capabilities or features.")
    Context: Optional[Any] = Field(None, description="Machine data configuration context")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device")
    IsApplicable: Optional[bool] = Field(None, description="Indicates whether the configuration or policy is applicable")
    IsCompliant: Optional[bool] = Field(None, description="Indicates whether the configuration or policy is properly configured")
    IsExpectedUserImpact: Optional[bool] = Field(None, description="Indicates if user impact is expected when configuration applied")
    OSPlatform: Optional[str] = Field(None, description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 10 and Windows 7")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
