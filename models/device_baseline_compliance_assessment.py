from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBaselineComplianceAssessment(BaseModel):
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device")
    OSPlatform: Optional[str] = Field(None, description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 11, Windows 10 and Windows 7.")
    OSVersion: Optional[str] = Field(None, description="Version of the operating system running on the device")
    ConfigurationId: Optional[str] = Field(None, description="Unique identifier for a specific configuration")
    ProfileId: Optional[str] = Field(None, description="Unique identifier for the profile")
    IsCompliant: Optional[bool] = Field(None, description="Indicates whether the device that initiated the event is compliant or not")
    IsApplicable: Optional[bool] = Field(None, description="Indicates whether the configuration or policy is applicable")
    Source: Optional[Any] = Field(None, description="The registry path or other location used to determine the current device setting")
    RecommendedValue: Optional[Any] = Field(None, description="Set of expected values for the current device setting to be compliant")
    CurrentValue: Optional[Any] = Field(None, description="Set of detected values found on the device")
    IsExempt: Optional[bool] = Field(None, description="Indicates whether the device is exempt from having the baseline configuration")
