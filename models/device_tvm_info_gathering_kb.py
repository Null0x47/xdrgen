from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmInfoGatheringKB(BaseModel):
    IgId: Optional[str] = Field(None, description="Unique identifier for the piece of information gathered")
    FieldName: Optional[str] = Field(None, description="Name of the field where this information appears in the AdditionalFields column of the DeviceTvmInfoGathering table")
    Description: Optional[str] = Field(None, description="Description of the information gathered")
    Categories: Optional[Any] = Field(None, description="List of categories that the information belongs to, in JSON array format")
    DataStructure: Optional[str] = Field(None, description="The data structure of the information gathered")
