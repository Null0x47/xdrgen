"""Generator registry — `@register("TableName")` populates GENERATORS."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from world import World

Generator = Callable[[World], BaseModel]
GENERATORS: dict[str, Generator] = {}


def register(table_name: str) -> Callable[[Generator], Generator]:
    def decorator(fn: Generator) -> Generator:
        GENERATORS[table_name] = fn
        return fn

    return decorator
