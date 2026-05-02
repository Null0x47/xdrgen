from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class ExposureGraphNodes(BaseModel):
    NodeId: Optional[str] = Field(None, description="Unique node identifier")
    NodeLabel: Optional[str] = Field(None, description="Node label")
    NodeName: Optional[str] = Field(None, description="Node display name")
    Categories: Optional[Any] = Field(
        None, description="Categories of the node in JSON format"
    )
    NodeProperties: Optional[Any] = Field(
        None,
        description="Properties of the node, including insights related to the resource, such as whether the resource is exposed to the internet, or vulnerable to remote code execution. Values are JSON formatted raw data (unstructured).",
    )
    EntityIds: Optional[Any] = Field(
        None, description="All known node identifiers in JSON format"
    )
