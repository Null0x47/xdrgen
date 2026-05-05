from __future__ import annotations

import json
import random

from generators.base import register
from generators.device_common import envelope, pick_device
from models import DeviceNetworkInfo
from world import World

# One row per adapter — Wi-Fi, wired LAN, VPN tunnel, virtual loopback.
_ADAPTERS = [
    {
        "name": "Wi-Fi",
        "type": "Wireless",
        "vendor": "Intel Corporation",
        "tunnel": None,
        "network_category": "Private",
        "network_name": "CONTOSO-CORP",
    },
    {
        "name": "Ethernet",
        "type": "Ethernet",
        "vendor": "Realtek Semiconductor",
        "tunnel": None,
        "network_category": "Domain",
        "network_name": "contoso.local",
    },
    {
        "name": "vEthernet (WSL)",
        "type": "Ethernet",
        "vendor": "Microsoft Corporation",
        "tunnel": None,
        "network_category": "Private",
        "network_name": "WSL Internal",
    },
    {
        "name": "Cisco AnyConnect VPN",
        "type": "Tunnel",
        "vendor": "Cisco Systems, Inc.",
        "tunnel": "Ssh",
        "network_category": "Domain",
        "network_name": "contoso-vpn",
    },
]

_DNS_SERVERS = ["10.0.0.10", "10.0.0.11", "8.8.8.8", "1.1.1.1"]
_DEFAULT_GATEWAYS = ["10.10.20.1", "10.10.30.1", "10.10.40.1"]


def _mac_addr() -> str:
    return "-".join(f"{random.randint(0, 255):02X}" for _ in range(6))


@register("DeviceNetworkInfo")
def generate(world: World) -> DeviceNetworkInfo:
    device = pick_device(world)
    adapter = random.choice(_ADAPTERS)

    local_ip = device.local_ip or f"10.10.20.{random.randint(2, 254)}"
    mac = device.mac_address or _mac_addr()

    ip_addresses = [
        {"IPAddress": local_ip, "SubnetPrefix": 24, "AddressType": "Private"},
        {
            "IPAddress": f"fe80::{random.randint(0x1000, 0xFFFF):x}",
            "SubnetPrefix": 64,
            "AddressType": "Private",
        },
    ]
    connected_networks = [
        {
            "Name": adapter["network_name"],
            "Category": adapter["network_category"],
            "Description": adapter["network_name"],
            "IsConnectedToInternet": adapter["tunnel"] is None,
        }
    ]

    return DeviceNetworkInfo(
        ConnectedNetworks=json.dumps(connected_networks),
        DefaultGateways=json.dumps([random.choice(_DEFAULT_GATEWAYS)]),
        DnsAddresses=json.dumps(random.sample(_DNS_SERVERS, k=2)),
        IPAddresses=json.dumps(ip_addresses),
        IPv4Dhcp=random.choice(_DEFAULT_GATEWAYS),
        IPv6Dhcp=None,
        MacAddress=mac,
        NetworkAdapterName=adapter["name"],
        NetworkAdapterStatus="Up",
        NetworkAdapterType=adapter["type"],
        NetworkAdapterVendor=adapter["vendor"],
        ReportId=random.randint(10**9, 10**10 - 1),
        TunnelType=adapter["tunnel"],
        Type="DeviceNetworkInfo",
        **envelope(world, device),
    )
