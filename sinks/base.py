"""Sink protocol — write(batch) zero+ times, close() once."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

Batch = list[tuple[str, BaseModel]]


class Sink(Protocol):
    def write(self, batch: Batch) -> None: ...
    def close(self) -> None: ...
