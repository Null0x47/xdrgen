from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceEtw(BaseModel):
    ActivityId: Optional[str] = Field(None, description="")
    appName: Optional[str] = Field(None, description="")
    Computer: Optional[str] = Field(None, description="")
    DeviceType: Optional[str] = Field(None, description="")
    EventId: Optional[int] = Field(None, description="")
    EventName: Optional[str] = Field(None, description="")
    period: Optional[int] = Field(None, description="")
    ProcessId: Optional[str] = Field(None, description="")
    ProviderId: Optional[str] = Field(None, description="")
    SerialNumber: Optional[str] = Field(None, description="")
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    status: Optional[int] = Field(None, description="")
    tags: Optional[str] = Field(None, description="")
    ThreadId: Optional[int] = Field(None, description="")
    TimeGenerated: Optional[datetime] = Field(None, description="")
    type: Optional[int] = Field(None, description="")
    Type: Optional[str] = Field(None, description="The name of the table")
    wakeEnabled: Optional[bool] = Field(None, description="")
