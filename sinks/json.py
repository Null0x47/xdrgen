"""JSON sink: one JSON-array file (default) or one file per event (--per-table)."""

from __future__ import annotations

import pathlib

from sinks.base import Batch, Sink


class JsonArraySink:
    """Streams events into one JSON-array file; flushes per batch."""

    def __init__(self, output: pathlib.Path) -> None:
        if output.parent != pathlib.Path(""):
            output.parent.mkdir(parents=True, exist_ok=True)
        self._f = output.open("w", encoding="utf-8")
        self._f.write("[")
        self._wrote_any = False

    def write(self, batch: Batch) -> None:
        for _table, event in batch:
            self._f.write(",\n  " if self._wrote_any else "\n  ")
            self._f.write(event.model_dump_json(by_alias=True))
            self._wrote_any = True
        self._f.flush()

    def close(self) -> None:
        self._f.write("\n]" if self._wrote_any else "]")
        self._f.close()


class PerTableJsonSink:
    """One JSON file per event: `{TableName}-{n:04d}.json` (counter is per-table)."""

    def __init__(self, output: pathlib.Path) -> None:
        output.mkdir(parents=True, exist_ok=True)
        self._dir = output
        self._counters: dict[str, int] = {}

    def write(self, batch: Batch) -> None:
        for table, event in batch:
            n = self._counters.get(table, 0)
            self._counters[table] = n + 1
            (self._dir / f"{table}-{n:04d}.json").write_text(
                event.model_dump_json(by_alias=True, indent=2),
                encoding="utf-8",
            )

    def close(self) -> None:
        return None


def build(output: pathlib.Path, per_table: bool) -> Sink:
    return PerTableJsonSink(output) if per_table else JsonArraySink(output)
