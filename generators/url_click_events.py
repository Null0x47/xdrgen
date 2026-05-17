from __future__ import annotations

import json
import random
import uuid

from models import UrlClickEvents
from generators.base import register
from generators.common import now_utc, pick, pick_filtered
from generators.email_pool import pool_for
from world import World

# Tied to a pool email so rows pivot to EmailEvents / EmailUrlInfo via
# NetworkMessageId.


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
    ip = pick(world.ips)
    timestamp = now_utc()

    outcome = pick(world.url_click_outcomes)
    action_type = outcome.action_type
    is_clicked_through = outcome.is_clicked_through
    threat_types_outcome = outcome.threat_types

    # Email's verdict overrides the rolled outcome — Safe Links blocks
    # known-phish URLs.
    threat_types = email["threat_types"] or threat_types_outcome
    if threat_types in ("Phish", "Malware"):
        chosen = pick_filtered(
            world.url_click_outcomes,
            lambda o: (
                (not o.is_clicked_through) or o.action_type == "BlockpageOverride"
            ),
        )
        action_type, is_clicked_through = chosen.action_type, chosen.is_clicked_through

    workload = pick(world.url_click_workloads).workload

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
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="UrlClickEvents",
        Url=url_entry["url"],
        UrlChain=_redirect_chain(url_entry["url"]),
        Workload=workload,
        TenantId=world.tenant_id,
    )
