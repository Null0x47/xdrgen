from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSoftwareInventory(BaseModel):
    DeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in the service"
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name (FQDN) of the device"
    )
    EndOfSupportDate: Optional[datetime] = Field(
        None,
        description="End-of-support (EOS) or end-of-life (EOL) date of the software product",
    )
    EndOfSupportStatus: Optional[str] = Field(
        None,
        description="Indicates the lifecycle stage of the software product relative to its specified end-of-support (EOS) or end-of-life (EOL) date",
    )
    OSArchitecture: Optional[str] = Field(
        None, description="Architecture of the operating system running on the machine"
    )
    OSPlatform: Optional[str] = Field(
        None,
        description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 10 and Windows 7",
    )
    OSVersion: Optional[str] = Field(
        None, description="Version of the operating system running on the machine"
    )
    ProductCodeCpe: Optional[str] = Field(
        None,
        description="The standard Common Platform Enumeration (CPE) name of the software product version",
    )
    SoftwareName: Optional[str] = Field(
        None, description="Name of the software product"
    )
    SoftwareVendor: Optional[str] = Field(
        None, description="Name of the software vendor"
    )
    SoftwareVersion: Optional[str] = Field(
        None, description="Version number of the software product"
    )
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(
        None, description="Date and time when the record was generated"
    )
    Type: Optional[str] = Field(None, description="The name of the table")
