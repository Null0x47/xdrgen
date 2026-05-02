"""Common telemetry helpers.

All tenant + fixture data has moved to `world.py` — generators read it via
the `World` object passed into each `generate()` call. This module is now
just the home for the `now_utc()` helper that every generator imports."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)
