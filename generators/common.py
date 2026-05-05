"""Shared `now_utc()` helper for generators."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)
