from __future__ import annotations

import json
import random

from generators.base import register
from generators.common import pick, pick_many
from generators.device_common import envelope, pick_device
from models import DeviceNetworkInfo
from world import World


def _mac_addr() -> str:
    return "-".join(f"{random.randint(0, 255):02X}" for _ in range(6))


@register("DeviceNetworkInfo")
def generate(world: World) -> DeviceNetworkInfo:
    device = pick_device(world)
    adapter = pick(world.network_adapters)

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
            "Name": adapter.network_name,
            "Category": adapter.network_category,
            "Description": adapter.network_name,
            "IsConnectedToInternet": adapter.tunnel is None,
        }
    ]

    dns_servers = [e.value for e in pick_many(world.local_dns_servers, 2)]
    return DeviceNetworkInfo(
        ConnectedNetworks=json.dumps(connected_networks),
        DefaultGateways=json.dumps([pick(world.local_default_gateways).value]),
        DnsAddresses=json.dumps(dns_servers),
        IPAddresses=json.dumps(ip_addresses),
        IPv4Dhcp=pick(world.local_default_gateways).value,
        IPv6Dhcp=None,
        MacAddress=mac,
        NetworkAdapterName=adapter.name,
        NetworkAdapterStatus="Up",
        NetworkAdapterType=adapter.type,
        NetworkAdapterVendor=adapter.vendor,
        ReportId=random.randint(10**9, 10**10 - 1),
        TunnelType=adapter.tunnel,
        Type="DeviceNetworkInfo",
        **envelope(world, device),
    )
