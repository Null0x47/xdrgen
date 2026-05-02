"""Generator registry — every telemetry generator decorates its `generate(world)`
function with `@register("TableName")` and the dict in this module is the
canonical source.

Decoupling the registry from `generators/__init__.py` lets that file act as a
thin auto-discoverer: it imports each submodule, the decorators populate
`GENERATORS` as a side effect.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from world import World

Generator = Callable[[World], BaseModel]
GENERATORS: dict[str, Generator] = {}


def register(table_name: str) -> Callable[[Generator], Generator]:
    """Register a generator function under the given Defender XDR table name."""

    def decorator(fn: Generator) -> Generator:
        GENERATORS[table_name] = fn
        return fn

    return decorator
