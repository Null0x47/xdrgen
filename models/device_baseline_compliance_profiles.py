from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBaselineComplianceProfiles(BaseModel):
    ProfileId: Optional[str] = Field(None, description="Unique identifier for the profile")
    ProfileName: Optional[str] = Field(None, description="Display name of the profile")
    ProfileDescription: Optional[str] = Field(None, description="Optional description providing additional information related to the profile")
    OSPlatform: Optional[Any] = Field(None, description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 11, Windows 10 and Windows 7.")
    OSVersion: Optional[str] = Field(None, description="Version of the operating system running on the device")
    BaseBenchmark: Optional[str] = Field(None, description="Industry benchmark on top of which the profile was created")
    BenchmarkVersion: Optional[str] = Field(None, description="Version of the industry benchmark on top of which the profile was created")
    BenchmarkProfileLevel: Optional[str] = Field(None, description="Benchmark compliance level set for the profile")
    Status: Optional[bool] = Field(None, description="Indicator of the profile status - can be Enabled or Disabled")
    CreatedBy: Optional[str] = Field(None, description="Identity of the user account who created the profile")
    CreatedOn: Optional[datetime] = Field(None, description="Date and time when the profile was created")
    LastUpdatedBy: Optional[str] = Field(None, description="Identity of the user account who last updated the profile")
    LastUpdatedOn: Optional[datetime] = Field(None, description="Date and time when the profile was last updated")
