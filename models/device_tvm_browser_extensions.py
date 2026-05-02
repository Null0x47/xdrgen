from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmBrowserExtensions(BaseModel):
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    BrowserName: Optional[str] = Field(None, description="Name of the web browser with the extension")
    ExtensionId: Optional[str] = Field(None, description="Unique identifier for the browser extension")
    ExtensionName: Optional[str] = Field(None, description="Name of the extension")
    ExtensionDescription: Optional[str] = Field(None, description="Description from the publisher about the extension")
    ExtensionVersion: Optional[str] = Field(None, description="Version number of the extension")
    ExtensionRisk: Optional[str] = Field(None, description="Risk level for the extension based on the permissions it has requested")
    ExtensionVendor: Optional[str] = Field(None, description="Name of the vendor offering the extension")
    IsActivated: Optional[str] = Field(None, description="Whether the extension is turned on or off on the devices")
    InstallationTime: Optional[datetime] = Field(None, description="Date and time when the browser extension was first installed")
