"""Sink protocol.

A `Sink` consumes batches of generated events and persists them somewhere
(JSON file, Kafka topic, …). New sinks plug in by implementing the protocol
and exposing a `build(...)` factory in their module — `main.py` picks one
based on the `--sink` flag.

Each batch is a list of `(table_name, event_model)` tuples. Sinks must accept
zero or more `write()` calls and exactly one `close()`.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

Batch = list[tuple[str, BaseModel]]


class Sink(Protocol):
    def write(self, batch: Batch) -> None: ...
    def close(self) -> None: ...
