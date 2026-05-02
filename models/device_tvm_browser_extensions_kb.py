from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmBrowserExtensionsKB(BaseModel):
    BrowserName: Optional[str] = Field(None, description="Name of the web browser with the extension")
    ExtensionId: Optional[str] = Field(None, description="Unique identifier for the browser extension")
    ExtensionName: Optional[str] = Field(None, description="Name of the extension")
    ExtensionDescription: Optional[str] = Field(None, description="Description from the publisher about the extension")
    ExtensionVersion: Optional[Any] = Field(None, description="Version number of the extension")
    ExtensionRisk: Optional[str] = Field(None, description="Risk level for the extension based on the permissions it has requested")
    PermissionId: Optional[str] = Field(None, description="Unique identifier for the permission")
    PermissionName: Optional[str] = Field(None, description="Name given to each permission based on what the extension is asking for")
    PermissionDescription: Optional[str] = Field(None, description="Explanation of what the permission is supposed to do")
    PermissionRisk: Optional[str] = Field(None, description="Risk level for the permission based on the type of access it would allow")
    IsPermissionRequired: Optional[str] = Field(None, description="Whether the permission is required for the extension to run, or optional")
