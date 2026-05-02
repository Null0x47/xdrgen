from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceEvents(BaseModel):
    AccountDomain: Optional[str] = Field(None, description="Domain of the account.")
    AccountName: Optional[str] = Field(None, description="User name of the account.")
    AccountSid: Optional[str] = Field(
        None, description="Security identifier (SID) of the account."
    )
    ActionType: Optional[str] = Field(
        None, description="Type of activity that triggered the event."
    )
    AdditionalFields: Optional[Any] = Field(
        None, description="Additional information about the entity or event."
    )
    AppGuardContainerId: Optional[str] = Field(
        None,
        description="Identifier for the virtualized container used by Application Guard to isolate browser activity.",
    )
    CreatedProcessSessionId: Optional[int] = Field(
        None, description="Windows session ID of the created process."
    )
    DeviceId: Optional[str] = Field(
        None, description="Unique identifier for the device in the service."
    )
    DeviceName: Optional[str] = Field(
        None, description="Fully qualified domain name (FQDN) of the device."
    )
    FileName: Optional[str] = Field(None, description="Domain of the account.")
    FileOriginIP: Optional[str] = Field(
        None, description="IP address where the file was downloaded from."
    )
    FileOriginUrl: Optional[str] = Field(
        None, description="URL where the file was downloaded from."
    )
    FileSize: Optional[int] = Field(None, description="Size of the file in bytes.")
    FolderPath: Optional[str] = Field(None, description="Domain of the account.")
    InitiatingProcessAccountDomain: Optional[str] = Field(
        None,
        description="Domain of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountName: Optional[str] = Field(
        None,
        description="User name of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountObjectId: Optional[str] = Field(
        None,
        description="Azure AD object ID of the user account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountSid: Optional[str] = Field(
        None,
        description="Security Identifier (SID) of the account that ran the process responsible for the event.",
    )
    InitiatingProcessAccountUpn: Optional[str] = Field(
        None,
        description="User principal name (UPN) of the account that ran the process responsible for the event.",
    )
    InitiatingProcessCommandLine: Optional[str] = Field(
        None,
        description="Command line used to run the process that initiated the event.",
    )
    InitiatingProcessCreationTime: Optional[datetime] = Field(
        None,
        description="Date and time when the process that initiated the event was started.",
    )
    InitiatingProcessFileName: Optional[str] = Field(
        None, description="Name of the process that initiated the event."
    )
    InitiatingProcessFileSize: Optional[int] = Field(
        None,
        description="Size in bytes of the file that ran the process responsible for the event.",
    )
    InitiatingProcessFolderPath: Optional[str] = Field(
        None,
        description="Folder containing the process (image file) that initiated the event.",
    )
    InitiatingProcessId: Optional[int] = Field(
        None, description="Process ID (PID) of the process that initiated the event."
    )
    InitiatingProcessLogonId: Optional[int] = Field(
        None,
        description="Identifier for a logon session of the process that initiated the event. This identifier is unique on the same machine only between restarts.",
    )
    InitiatingProcessMD5: Optional[str] = Field(
        None,
        description="MD5 hash of the process (image file) that initiated the event.",
    )
    InitiatingProcessParentCreationTime: Optional[datetime] = Field(
        None,
        description="Date and time when the parent of the process responsible for the event was started.",
    )
    InitiatingProcessParentFileName: Optional[str] = Field(
        None,
        description="Name of the parent process that spawned the process responsible for the event.",
    )
    InitiatingProcessParentId: Optional[int] = Field(
        None,
        description="Process ID (PID) of the parent process that spawned the process responsible for the event.",
    )
    InitiatingProcessRemoteSessionDeviceName: Optional[str] = Field(
        None,
        description="Device name of the remote device from which the initiating process's RDP session was initiated.",
    )
    InitiatingProcessRemoteSessionIP: Optional[str] = Field(
        None,
        description="IP address of the remote device from which the initiating process's RDP session was initiated.",
    )
    InitiatingProcessSessionId: Optional[int] = Field(
        None, description="Windows session ID of the initiating process."
    )
    InitiatingProcessSHA1: Optional[str] = Field(
        None,
        description="SHA-1 hash of the process (image file) that initiated the event.",
    )
    InitiatingProcessSHA256: Optional[str] = Field(
        None,
        description="SHA-256 hash of the process (image file) that initiated the event. This field is usually not populated - use the SHA1 column when available.",
    )
    InitiatingProcessUniqueId: Optional[str] = Field(
        None,
        description="Unique identifier of the initiating process; this is equal to the Process Start Key in Windows devices.",
    )
    InitiatingProcessVersionInfoCompanyName: Optional[str] = Field(
        None,
        description="Company name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoFileDescription: Optional[str] = Field(
        None,
        description="Description from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoInternalFileName: Optional[str] = Field(
        None,
        description="Internal file name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoOriginalFileName: Optional[str] = Field(
        None,
        description="Original file name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoProductName: Optional[str] = Field(
        None,
        description="Product name from the version information of the process (image file) responsible for the event.",
    )
    InitiatingProcessVersionInfoProductVersion: Optional[str] = Field(
        None,
        description="Product version from the version information of the process (image file) responsible for the event.",
    )
    IsInitiatingProcessRemoteSession: Optional[bool] = Field(
        None,
        description="Indicates whether the initiating process was run under a remote desktop protocol (RDP) session (true) or locally (false).",
    )
    IsProcessRemoteSession: Optional[bool] = Field(
        None,
        description="Indicates whether the created process was run under a remote desktop protocol (RDP) session (true) or locally (false).",
    )
    LocalIP: Optional[str] = Field(
        None,
        description="IP address assigned to the local machine used during communication.",
    )
    LocalPort: Optional[int] = Field(
        None, description="TCP port on the local machine used during communication."
    )
    LogonId: Optional[int] = Field(
        None,
        description="Identifier for a logon session. This identifier is unique on the same machine only between restarts.",
    )
    MachineGroup: Optional[str] = Field(
        None,
        description="Machine group of the machine. This group is used by role-based access control to determine access to the machine.",
    )
    MD5: Optional[str] = Field(
        None,
        description="MD5 hash of the file that the recorded action was applied to.",
    )
    ProcessCommandLine: Optional[str] = Field(
        None, description="Command line used to create the new process."
    )
    ProcessCreationTime: Optional[datetime] = Field(
        None, description="Date and time the process was created."
    )
    ProcessId: Optional[int] = Field(
        None, description="Process ID (PID) of the newly created process."
    )
    ProcessRemoteSessionDeviceName: Optional[str] = Field(
        None,
        description="Device name of the remote device from which the created process's RDP session was initiated.",
    )
    ProcessRemoteSessionIP: Optional[str] = Field(
        None,
        description="IP address of the remote device from which the created process's RDP session was initiated.",
    )
    ProcessTokenElevation: Optional[str] = Field(
        None,
        description="Token type indicating the presence or absence of User Access Control (UAC) privilege elevation applied to the newly created process.",
    )
    RegistryKey: Optional[str] = Field(
        None, description="Registry key that the recorded action was applied to."
    )
    RegistryValueData: Optional[str] = Field(
        None,
        description="Data of the registry value that the recorded action was applied to.",
    )
    RegistryValueName: Optional[str] = Field(
        None,
        description="Name of the registry value that the recorded action was applied to.",
    )
    RemoteDeviceName: Optional[str] = Field(
        None,
        description="Name of the device that performed a remote operation on the affected machine. Depending on the event being reported, this name could be a fully-qualified domain name (FQDN), a NetBIOS name, or a host name without domain information..",
    )
    RemoteIP: Optional[str] = Field(
        None, description="IP address that was being connected to."
    )
    RemotePort: Optional[int] = Field(
        None, description="TCP port on the remote device that was being connected to."
    )
    RemoteUrl: Optional[str] = Field(
        None,
        description="URL or fully qualified domain name (FQDN) that was being connected to.",
    )
    ReportId: Optional[int] = Field(
        None,
        description="Event identifier based on a repeating counter. To identify unique events, this column must be used in conjunction with the ComputerName and EventTime columns.",
    )
    SHA1: Optional[str] = Field(
        None,
        description="SHA-1 hash of the file that the recorded action was applied to.",
    )
    SHA256: Optional[str] = Field(
        None, description="SHA-256 of the file that the recorded action was applied to."
    )
    SourceSystem: Optional[str] = Field(
        None,
        description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics",
    )
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(
        None,
        description="Date and time the event was recorded by the MDE agent on the endpoint.",
    )
    Type: Optional[str] = Field(None, description="The name of the table")
