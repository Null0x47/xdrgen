"""CSV sink: one CSV file (default) or one file per event (--per-table)."""

from __future__ import annotations

import csv
import json
import pathlib
from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from sinks.base import Batch, Sink


def _column_name(field_name: str, info: FieldInfo) -> str:
    return info.alias or field_name


def _columns_for_model(cls: type[BaseModel]) -> list[str]:
    return [_column_name(name, info) for name, info in cls.model_fields.items()]


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value


class CsvSingleFileSink:
    """Streams events into one CSV file: `_table,event_json`; flushes per batch."""

    def __init__(self, output: pathlib.Path) -> None:
        if output.parent != pathlib.Path(""):
            output.parent.mkdir(parents=True, exist_ok=True)
        self._f = output.open("w", encoding="utf-8", newline="")
        self._writer = csv.writer(self._f)
        self._writer.writerow(["_table", "event_json"])

    def write(self, batch: Batch) -> None:
        for table, event in batch:
            self._writer.writerow([table, event.model_dump_json(by_alias=True)])
        self._f.flush()

    def close(self) -> None:
        self._f.close()


class PerTableCsvSink:
    """One CSV file per event: `{TableName}-{n:04d}.csv` (counter is per-table)."""

    def __init__(self, output: pathlib.Path) -> None:
        output.mkdir(parents=True, exist_ok=True)
        self._dir = output
        self._counters: dict[str, int] = {}
        self._columns_cache: dict[type[BaseModel], list[str]] = {}

    def _columns_for(self, cls: type[BaseModel]) -> list[str]:
        cached = self._columns_cache.get(cls)
        if cached is None:
            cached = _columns_for_model(cls)
            self._columns_cache[cls] = cached
        return cached

    def write(self, batch: Batch) -> None:
        for table, event in batch:
            n = self._counters.get(table, 0)
            self._counters[table] = n + 1
            columns = self._columns_for(type(event))
            data = event.model_dump(by_alias=True, mode="json")
            row = [_csv_value(data.get(col)) for col in columns]
            path = self._dir / f"{table}-{n:04d}.csv"
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerow(row)

    def close(self) -> None:
        return None


def build(output: pathlib.Path, per_table: bool) -> Sink:
    return PerTableCsvSink(output) if per_table else CsvSingleFileSink(output)
