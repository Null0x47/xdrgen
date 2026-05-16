from __future__ import annotations

import random

from models import EmailUrlInfo
from generators.base import register
from generators.common import now_utc
from generators.email_pool import pool_for
from world import World


@register("EmailUrlInfo")
def generate(world: World) -> EmailUrlInfo:
    email = pool_for(world).pick_with_urls()
    url = random.choice(email["urls"])
    timestamp = now_utc()

    return EmailUrlInfo(
        NetworkMessageId=email["network_message_id"],
        ReportId=str(random.randint(10**15, 10**16 - 1)),
        SourceSystem="Azure",
        TenantId=world.tenant_id,
        Timestamp=timestamp,
        TimeGenerated=timestamp,
        Type="EmailUrlInfo",
        Url=url["url"],
        UrlDomain=url["domain"],
        UrlLocation=url["location"],
    )
