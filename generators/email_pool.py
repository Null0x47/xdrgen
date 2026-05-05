"""Shared email pool for Email* / UrlClickEvents generators.

Every email-side table joins on `NetworkMessageId`, so all generators draw
from one finite pool of pre-built emails. `pool_for(world)` returns the
per-World singleton with personas resolved against `world.users` and
templates pulled from `world.email_templates`.
"""

from __future__ import annotations

import functools
import hashlib
import random
import uuid
from typing import Any

from world import User, World


def _sha256_hex(name: str) -> str:
    # Stable per-filename so the same attachment hashes the same across rows.
    return hashlib.sha256(f"contoso::{name}".encode()).hexdigest()


def _new_network_message_id() -> str:
    return str(uuid.uuid4())


def _new_internet_message_id(domain: str) -> str:
    # RFC 5322 message-id: <token@domain>.
    return f"<{uuid.uuid4().hex}@{domain}>"


def _resolve_recipient(persona: str, users: tuple[User, ...]) -> User:
    # Hash-index fallback when the persona has been removed from the world.
    match = next((u for u in users if u.sam_account_name == persona), None)
    if match is not None:
        return match
    return users[hash(persona) % len(users)]


class EmailPool:
    """Per-World email pool — resolves recipients and mints stable IDs once."""

    def __init__(self, world: World) -> None:
        resolved: list[dict[str, Any]] = []
        for tpl in world.email_templates:
            entry = tpl.model_dump()
            entry["network_message_id"] = _new_network_message_id()
            entry["internet_message_id"] = _new_internet_message_id(
                tpl.sender_mail_from_domain
            )
            entry["attachments"] = [
                {**a, "sha256": _sha256_hex(a["file_name"])}
                for a in entry["attachments"]
            ]
            entry["urls"] = list(entry["urls"])
            entry["recipient"] = _resolve_recipient(tpl.recipient_persona, world.users)
            resolved.append(entry)
        self.entries: tuple[dict[str, Any], ...] = tuple(resolved)

    def pick(self) -> dict[str, Any]:
        return random.choice(self.entries)

    def pick_with_attachments(self) -> dict[str, Any]:
        candidates = [e for e in self.entries if e["attachments"]]
        return random.choice(candidates)

    def pick_with_urls(self) -> dict[str, Any]:
        candidates = [e for e in self.entries if e["urls"]]
        return random.choice(candidates)


@functools.lru_cache(maxsize=4)
def pool_for(world: World) -> EmailPool:
    # Cached on World (frozen + hashable) — one pool per generate run.
    return EmailPool(world)
