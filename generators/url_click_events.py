from __future__ import annotations

import json
import random
import uuid

from models import UrlClickEvents
from generators.base import register
from generators.common import now_utc
from generators.email_pool import pool_for
from world import World

# Tied to a pool email so rows pivot to EmailEvents / EmailUrlInfo via
# NetworkMessageId.

# (ActionType, IsClickedThrough, ThreatTypes, weight)
_CLICK_OUTCOMES = [
    ("ClickAllowed", True, None, 86),
    ("Blockpage", False, "Phish", 5),
    ("BlockpageOverride", True, "Phish", 2),
    ("ClickBlocked", False, "Malware", 3),
    ("PendingDetonationPage", True, None, 4),
]
_OUTCOME_VALUES = list(range(len(_CLICK_OUTCOMES)))
_OUTCOME_WEIGHTS = [c[3] for c in _CLICK_OUTCOMES]

# Source workload weights — Email dominates.
_WORKLOADS = [
    ("Email", 75),
    ("Office", 12),
    ("Teams", 13),
]
_WORKLOAD_VALUES, _WORKLOAD_WEIGHTS = zip(*_WORKLOADS)


def _redirect_chain(url: str) -> str:
    """JSON array: [safelinks, (optional tracker), final URL]."""
    safelinks = f"https://eur01.safelinks.protection.outlook.com/?url={url}&data={uuid.uuid4().hex[:16]}"
    if random.random() < 0.3:
        chain = [safelinks, f"https://t.co/{uuid.uuid4().hex[:8]}", url]
    else:
        chain = [safelinks, url]
    return json.dumps(chain)


@register("UrlClickEvents")
def generate(world: World) -> UrlClickEvents:
    email = pool_for(world).pick_with_urls()
    url_entry = random.choice(email["urls"])
    recipient = email["recipient"]
    ip = random.choice(world.ips)
    timestamp = now_utc()

    idx = random.choices(_OUTCOME_VALUES, weights=_OUTCOME_WEIGHTS, k=1)[0]
    action_type, is_clicked_through, threat_types_outcome, _ = _CLICK_OUTCOMES[idx]

    # Email's verdict overrides the rolled outcome — Safe Links blocks
    # known-phish URLs.
    threat_types = email["threat_types"] or threat_types_outcome
    if threat_types in ("Phish", "Malware"):
        action_type, is_clicked_through = random.choice(
            [
                ("Blockpage", False),
                ("ClickBlocked", False),
                ("BlockpageOverride", True),
            ]
        )

    workload = random.choices(_WORKLOAD_VALUES, weights=_WORKLOAD_WEIGHTS, k=1)[0]

    detection_methods = email["detection_methods"] if threat_types else None

    return UrlClickEvents(
        AccountUpn=recipient.upn,
        ActionType=action_type,
        AppName="Outlook" if workload == "Email" else workload,
        AppVersion="16.0.17328.20214" if workload == "Email" else "1.6.00.27563",
        DetectionMethods=detection_methods,
        IPAddress=ip.ip,
        IsClickedThrough=is_clicked_through,
        NetworkMessageId=email["network_message_id"],
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceId=str(uuid.uuid4()),
        SourceSystem="Azure",
        ThreatTypes=threat_types,
        TimeGenerated=timestamp,
        Type="UrlClickEvents",
        Url=url_entry["url"],
        UrlChain=_redirect_chain(url_entry["url"]),
        Workload=workload,
        TenantId=world.tenant_id,
    )
