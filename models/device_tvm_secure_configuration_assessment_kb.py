from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmSecureConfigurationAssessmentKB(BaseModel):
    ConfigurationBenchmarks: Optional[Any] = Field(None, description="List of industry benchmarks which recommend the same or similar configuration.")
    ConfigurationCategory: Optional[str] = Field(None, description="Category or grouping to which the configuration belongs.")
    ConfigurationDescription: Optional[str] = Field(None, description="Description of the configuration.")
    ConfigurationId: Optional[str] = Field(None, description="Unique identifier for a specific configuration.")
    ConfigurationImpact: Optional[float] = Field(None, description="Rated impact of the configuration to the overall configuration score (1-10).")
    ConfigurationName: Optional[str] = Field(None, description="Display name of the configuration.")
    ConfigurationSubcategory: Optional[str] = Field(None, description="Subcategory or subgrouping to which the configuration belongs. Commonly, this describes specific capabilities or features.")
    RelatedMitreTactics: Optional[Any] = Field(None, description="Related tactics from Mitre knowledge base.")
    RelatedMitreTechniques: Optional[Any] = Field(None, description="Related techniques from Mitre knowledge base.")
    RemediationOptions: Optional[str] = Field(None, description="Recommended actions to reduce or address any associated risks")
    RiskDescription: Optional[str] = Field(None, description="Description of any associated risks.")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    Tags: Optional[Any] = Field(None, description="Labels representing various attributes, used to identify or categorize a security configuration.")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time when the record was generated.")
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    Type: Optional[str] = Field(None, description="The name of the table")
