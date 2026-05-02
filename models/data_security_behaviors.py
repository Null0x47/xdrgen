from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DataSecurityBehaviors(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the record was generated or updated")
    BehaviorId: Optional[str] = Field(None, description="Unique identifier for the behavior")
    ActionType: Optional[str] = Field(None, description="Type of behavior. Refer to the catalog of behaviors detected by Microsoft Purview Insider Risk Management.")
    StartTime: Optional[datetime] = Field(None, description="Date and time of the first activity related to the behavior")
    EndTime: Optional[datetime] = Field(None, description="Date and time of the last activity related to the behavior")
    AttackTechniques: Optional[str] = Field(None, description="MITRE ATT&CK techniques associated with the activity that triggered the behavior. Refer to subtechniques in the insider risk management behavior catalog.")
    Categories: Optional[str] = Field(None, description="Type of threat indicator or breach activity identified by the behavior")
    ActionCategory: Optional[str] = Field(None, description="Category of action that triggered the event")
    Description: Optional[str] = Field(None, description="Description of the behavior")
    ServiceSource: Optional[str] = Field(None, description="Product or service that identified the behavior")
    DetectionSource: Optional[str] = Field(None, description="Detection technology or sensor that identified the notable component or activity")
    ActivityCount: Optional[int] = Field(None, description="Total user activity events recorded under this behavior")
    IsAnomalous: Optional[bool] = Field(None, description="Indicates if this behavior is anomalous (1) or not (0)")
    IsContentHidden: Optional[bool] = Field(None, description="Indicates if the behavior involves hidden content on a device")
    AccountUpn: Optional[str] = Field(None, description="User principal name (UPN) of the account")
    AccountEmail: Optional[str] = Field(None, description="Email address of the account")
    Application: Optional[str] = Field(None, description="Application that performed the recorded action")
    DeviceInfo: Optional[Any] = Field(None, description="List of device information for the device involved in this behavior, including device ID, device name, and the number of events in which the device is involved; in JSON array format")
    SensitivityLabelInfo: Optional[Any] = Field(None, description="List of sensitivity labels assigned to content involved in this behavior, including the unique identifier for the Microsoft Information Protection sensitivity label assigned to the related content, the name of the sensitivity label, and the number of events in the behavior involving this label; in JSON array format")
    SensitiveInfoTypesInfo: Optional[Any] = Field(None, description="List of sensitive info types detected in the content involved in this behavior, including the unique identifier for the sensitive info type, the name of the sensitive info type, and the number of events in the behavior involving this sensitive info type; in JSON array format")
    UrlDomainInfo: Optional[Any] = Field(None, description="List of websites or service URLs involved in the behavior, including the name of the URL domain, the direction of data (sent or received from domain), type of URL domain (customer-configured or based on watchlists), and the number of events in the behavior involving the specific domain; in JSON array format")
    SharepointSiteInfo: Optional[Any] = Field(None, description="List of SharePoint sites involved in this behavior, including the unique identifier for the SharePoint site, the name of the SharePoint site, and the number of events in the behavior involving the SharePoint site; in JSON array format")
    RecipientEmailInfo: Optional[Any] = Field(None, description="List of information about the recipient involved in the behavior, including the email address of the recipient and the number of events in the behavior involving the recipient; in JSON array format")
    RemovableMediaInfo: Optional[Any] = Field(None, description="List of any removable media involved in the behavior, including the serial number of the removable media device, the manufacturer of the removable media device, and the model of the removable device; in JSON array format")
    PrinterName: Optional[Any] = Field(None, description="List of printers involved in the behavior; in array format")
    PriorityContentMatchInfo: Optional[Any] = Field(None, description="List of priority content matches identified within this behavior and their associated details. Priority content definitions are done by the admins for each Insider risk management policy. Displayed in JSON array format.")
