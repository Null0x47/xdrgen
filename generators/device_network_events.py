from __future__ import annotations

import random

from generators.base import register
from generators.device_common import (
    envelope,
    initiating_process_fields,
    pick_device,
    pick_user_for_device,
)
from models import DeviceNetworkEvents
from world import World


def _ip_type(ip: str) -> str:
    if ip.startswith(("10.", "192.168.", "172.16.", "172.17.")):
        return "Private"
    if ip.startswith("127."):
        return "Loopback"
    return "Public"


@register("DeviceNetworkEvents")
def generate(world: World) -> DeviceNetworkEvents:
    device = pick_device(world)
    user = pick_user_for_device(world, device)
    remote_ip_entry = random.choice(world.ips)

    action_type = random.choices(
        [a.action for a in world.device_network_action_types],
        weights=[a.weight for a in world.device_network_action_types],
        k=1,
    )[0]
    destination = random.choice(world.network_destinations)
    remote_port, remote_url = destination.port, destination.url
    protocol = "Udp" if remote_port == 53 else "Tcp"

    local_ip = device.local_ip or f"10.10.20.{random.randint(2, 254)}"

    return DeviceNetworkEvents(
        ActionType=action_type,
        AdditionalFields=None,
        AppGuardContainerId=None,
        LocalIP=local_ip,
        LocalIPType="Private",
        LocalPort=random.randint(49152, 65535),
        Protocol=protocol,
        RemoteIP=remote_ip_entry.ip,
        RemoteIPType=_ip_type(remote_ip_entry.ip),
        RemotePort=remote_port,
        RemoteUrl=remote_url,
        ReportId=random.randint(10**9, 10**10 - 1),
        Type="DeviceNetworkEvents",
        **initiating_process_fields(world, user, integrity_and_elevation=True),
        **envelope(world, device),
    )
