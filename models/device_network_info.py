from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceNetworkInfo(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    ConnectedNetworks: Optional[Any] = Field(None, description="Networks that the adapter is connected to. Each JSON element in the array contains the network name, category (public, private or domain), a description, and a flag indicating if it is connected publicly to the internet.")
    DefaultGateways: Optional[Any] = Field(None, description="Default gateway addresses in JSON array format.")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service.")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device.")
    DnsAddresses: Optional[Any] = Field(None, description="DNS server addresses in JSON array format.")
    IPAddresses: Optional[Any] = Field(None, description="JSON array containing all the IP addresses assigned to the adapter, along with their respective subnet prefix and the IP class (RFC 1918 & RFC 4291).")
    IPv4Dhcp: Optional[str] = Field(None, description="IPv4 address of the configured DHCP server.")
    IPv6Dhcp: Optional[str] = Field(None, description="IPv6 address of the configured DHCP server.")
    MacAddress: Optional[str] = Field(None, description="MAC address of the network adapter.")
    MachineGroup: Optional[str] = Field(None, description="The machine-group which this machine is associated to. This group is used by role-based access control to determine access to the machine.")
    NetworkAdapterName: Optional[str] = Field(None, description="Name of the network adapter.")
    NetworkAdapterStatus: Optional[str] = Field(None, description="Operational status of the network adapter.")
    NetworkAdapterType: Optional[str] = Field(None, description="Network adapter type.")
    NetworkAdapterVendor: Optional[str] = Field(None, description="Name of the manufacturer or vendor of the network adapter.")
    ReportId: Optional[int] = Field(None, description="Event identifier based on a repeating counter. To identify unique events, this column must be used in conjunction with the DeviceName and/or Timestamp columns.")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time the event was recorded by the MDE agent on the endpoint.")
    TunnelType: Optional[str] = Field(None, description="Tunneling protocol, when the interface is used for this purpose, for example 6to4, Teredo, ISATAP, PPTP, SSTP, and SSH.")
    Type: Optional[str] = Field(None, description="The name of the table")
