from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class ExposureGraphEdges(BaseModel):
    EdgeId: Optional[str] = Field(None, description="Unique identifier for the relationship/edge")
    EdgeLabel: Optional[str] = Field(None, description="The edge label like \"routes traffic to\"")
    SourceNodeId: Optional[str] = Field(None, description="Node ID of the edge's source")
    SourceNodeName: Optional[str] = Field(None, description="Source node display name")
    SourceNodeLabel: Optional[str] = Field(None, description="Source node label")
    SourceNodeCategories: Optional[Any] = Field(None, description="Categories list of the source node in JSON format")
    TargetNodeId: Optional[str] = Field(None, description="Node ID of the edge's target")
    TargetNodeName: Optional[str] = Field(None, description="Display name of the target node")
    TargetNodeLabel: Optional[str] = Field(None, description="Target node label")
    TargetNodeCategories: Optional[Any] = Field(None, description="The categories list of the target node in JSON format")
    EdgeProperties: Optional[Any] = Field(None, description="Optional data relevant for the relationship between the nodes in JSON format")
