"""File-based sinks.

Two flavours, picked by the `per_table` flag in `build()`:

- `JsonArrayFileSink` — streams every event into one JSON array file, flushed
  on every batch so memory stays bounded across long runs.
- `PerTableFileSink` — writes one `{TableName}-{n:04d}.json` file per event
  inside the output directory, with `n` scoped per table.
"""

from __future__ import annotations

import pathlib

from sinks.base import Batch, Sink


class JsonArrayFileSink:
    """Streams events into a single JSON-array file.

    Wire format:

        [
          {"<event-fields>"},
          {"<event-fields>"}
        ]

    Each `write(batch)` appends and `flush()`es immediately, so memory stays
    bounded regardless of run length. `close()` writes the trailing `]` and
    is safe to call when no events were ever written (emits `[]`).
    """

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


class PerTableFileSink:
    """Writes one JSON file per event, named `{TableName}-{n:04d}.json` in
    the output directory. The counter is scoped per table so filenames stay
    stable across tables sharing the directory."""

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
    return PerTableFileSink(output) if per_table else JsonArrayFileSink(output)
