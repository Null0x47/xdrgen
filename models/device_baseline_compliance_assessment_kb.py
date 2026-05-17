from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBaselineComplianceAssessmentKB(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ConfigurationId: Optional[str] = Field(None, description="Unique identifier for a specific configuration")
    ConfigurationName: Optional[str] = Field(None, description="Display name of the configuration")
    ConfigurationDescription: Optional[str] = Field(None, description="Description of the configuration")
    ConfigurationRationale: Optional[str] = Field(None, description="Description of any associated risks and rationale behind the configuration")
    ConfigurationCategory: Optional[str] = Field(None, description="Category or grouping to which the configuration belongs")
    BenchmarkProfileLevels: Optional[Any] = Field(None, description="List of benchmark compliance levels for which the configuration is applicable")
    CCEReference: Optional[str] = Field(None, description="Unique Common Configuration Enumeration (CCE) identifier for the configuration")
    RemediationOptions: Optional[str] = Field(None, description="Recommended actions to reduce or address any associated risks")
    ConfigurationBenchmark: Optional[str] = Field(None, description="Industry benchmark recommending the configuration")
    Source: Optional[Any] = Field(None, description="The registry path or other location used to determine the current device setting")
    RecommendedValue: Optional[Any] = Field(None, description="Set of expected values for the current device setting to be compliant")
