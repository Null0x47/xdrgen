from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmHardwareFirmware(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device")
    ComponentType: Optional[str] = Field(None, description="Type of hardware or firmware component")
    Manufacturer: Optional[str] = Field(None, description="Manufacturer of hardware or firmware component")
    ComponentName: Optional[str] = Field(None, description="Name of hardware or firmware component")
    ComponentFamily: Optional[str] = Field(None, description="Component family or class, a grouping of components that have similar features or characteristics as determined by the manufacturer")
    ComponentVersion: Optional[str] = Field(None, description="Component version (for example, BIOS version)")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the components in JSON array format")
