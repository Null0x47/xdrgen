from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceConnectSession(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    Computer: Optional[str] = Field(None, description="")
    DeviceType: Optional[str] = Field(None, description="")
    EventId: Optional[int] = Field(None, description="")
    EventName: Optional[str] = Field(None, description="")
    HealthServiceId: Optional[str] = Field(None, description="")
    Opcode: Optional[int] = Field(None, description="")
    ProviderId: Optional[str] = Field(None, description="")
    SerialNumber: Optional[str] = Field(None, description="")
    sessionClass: Optional[str] = Field(None, description="")
    sessionConnected: Optional[bool] = Field(None, description="")
    sessionDurationMilliSeconds: Optional[float] = Field(None, description="")
    sessionType: Optional[str] = Field(None, description="")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TimeGenerated: Optional[datetime] = Field(None, description="")
    Type: Optional[str] = Field(None, description="The name of the table")
    wasCleanShutdown: Optional[bool] = Field(None, description="")
