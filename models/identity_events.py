from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class IdentityEvents(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated")
    ReportId: Optional[str] = Field(None, description="Unique identifier for the event")
    AccountId: Optional[str] = Field(None, description="Unique identifier for the account in the source application")
    AccountType: Optional[str] = Field(None, description="Type of user account, indicating its general role like User, SystemPrincipal")
    AccountDisplayName: Optional[str] = Field(None, description="Name displayed in the address book entry for the account user. This is usually a combination of the given name, middle initial, and surname of the user.")
    AccountUpn: Optional[str] = Field(None, description="Alternate ID, email, or name for the account in the source application")
    ActionType: Optional[str] = Field(None, description="Type of activity that triggered the event in the raw format received from the source application")
    ActionResult: Optional[str] = Field(None, description="Result of the action")
    ActionFailureReason: Optional[str] = Field(None, description="Information explaining why the recorded action failed")
    IPAddress: Optional[str] = Field(None, description="IP address assigned to the device and used during related network communications")
    UserAgent: Optional[str] = Field(None, description="User agent information from the web browser or other client application")
    TargetObjects: Optional[Any] = Field(None, description="List of the target objects of this activity. Target object can be user, group, role, domain, application, and more.")
    Application: Optional[str] = Field(None, description="The source application where this event was received from")
    ApplicationInstanceId: Optional[str] = Field(None, description="Domain of the source application")
    ApplicationEventId: Optional[str] = Field(None, description="Raw event ID provided by the source application")
    ApplicationSessionId: Optional[str] = Field(None, description="Raw session ID provided by the source application")
    RawEventData: Optional[Any] = Field(None, description="Full raw event information from the source application in JSON format")
    AdditionalFields: Optional[Any] = Field(None, description="Additional information about the entity or event")
