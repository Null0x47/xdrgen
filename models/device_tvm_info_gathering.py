from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmInfoGathering(BaseModel):
    Timestamp: Optional[datetime] = Field(
        None, description="Date and time when the record was generated"
    )
    LastSeenTime: Optional[datetime] = Field(
        None, description="Date and time when the service last saw the device"
    )
    DeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in the service"
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name (FQDN) of the device"
    )
    OSPlatform: Optional[str] = Field(
        None,
        description="Platform of the operating system running on the device. This indicates specific operating systems, including variations within the same family, such as Windows 10 and Windows 7.",
    )
    AdditionalFields: Optional[Any] = Field(
        None, description="Additional information about the entity or event"
    )
