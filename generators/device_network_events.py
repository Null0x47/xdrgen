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

# Weighted ActionType — outbound success dominates; rest is failures + inbound.
_ACTION_TYPES = [
    ("ConnectionSuccess", 60),
    ("ConnectionFailed", 8),
    ("ConnectionAttempt", 6),
    ("ConnectionRequest", 4),
    ("InboundConnectionAccepted", 6),
    ("ListeningConnectionCreated", 4),
    ("DnsConnectionInspected", 8),
    ("ConnectionFound", 4),
]
_ACTION_VALUES, _ACTION_WEIGHTS = zip(*_ACTION_TYPES)

# (port, host) pairs — host is None when the port is unrelated to a URL.
_REMOTE_DESTS = [
    (443, "graph.microsoft.com"),
    (443, "outlook.office365.com"),
    (443, "login.microsoftonline.com"),
    (443, "github.com"),
    (443, "api.github.com"),
    (443, "windowsupdate.microsoft.com"),
    (53, None),  # DNS
    (445, None),  # SMB
    (88, None),  # Kerberos
    (389, None),  # LDAP
    (3389, None),  # RDP
    (80, "ctldl.windowsupdate.com"),
]


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

    action_type = random.choices(_ACTION_VALUES, weights=_ACTION_WEIGHTS, k=1)[0]
    remote_port, remote_url = random.choice(_REMOTE_DESTS)
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
