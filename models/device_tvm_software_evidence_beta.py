from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSoftwareEvidenceBeta(BaseModel):
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    SoftwareVendor: Optional[str] = Field(None, description="Name of the software publisher")
    SoftwareName: Optional[str] = Field(None, description="Name of the software product")
    SoftwareVersion: Optional[str] = Field(None, description="Version number of the software product")
    RegistryPaths: Optional[Any] = Field(None, description="Registry paths where evidence indicating the existence of the software on a device was detected")
    DiskPaths: Optional[Any] = Field(None, description="Disk paths where file-level evidence indicating the existence of the software on a device was detected")
    LastSeenTime: Optional[str] = Field(None, description="Date and time when the device was last seen by this service")
