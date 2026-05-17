"""Shared helpers for generators."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Callable, TypeVar

from world import WeightedPool

T = TypeVar("T")


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def pick(pool: WeightedPool[T]) -> T:
    """Pick one entry from a pool. Honors `pool.random`: uniform when True,
    weighted (via per-entry `weight`) when False."""
    if pool.random:
        return random.choice(pool.entries)
    return random.choices(
        pool.entries,
        weights=[e.weight for e in pool.entries],
        k=1,
    )[0]


def pick_many(pool: WeightedPool[T], k: int) -> list[T]:
    """Pick `k` distinct entries from a pool. Sampling is always uniform —
    weighted sampling-without-replacement has no stdlib primitive, so
    per-entry `weight` is ignored for k>1 calls (the `random=false`
    validator still enforces weights are present)."""
    if not pool.entries:
        return []
    return random.sample(pool.entries, k=min(k, len(pool.entries)))


def pick_filtered(
    pool: WeightedPool[T],
    predicate: Callable[[T], bool],
) -> T:
    """Pick one entry matching `predicate`. Falls back to the full pool when
    no entry matches. Sampling mode (uniform vs weighted) is inherited
    from the original pool."""
    matches = tuple(e for e in pool.entries if predicate(e))
    if not matches:
        return pick(pool)
    if pool.random:
        return random.choice(matches)
    return random.choices(
        matches,
        weights=[e.weight for e in matches],
        k=1,
    )[0]
