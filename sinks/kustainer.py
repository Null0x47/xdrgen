"""Kustainer sink.

Pushes generated events into a local
[Kustainer](https://learn.microsoft.com/en-us/azure/data-explorer/kusto-emulator-overview)
instance — Microsoft's official Kusto/ADX emulator. Each event lands in the
table named after its Pydantic model (e.g. `CloudAppEvents` → `CloudAppEvents`).

The emulator does not implement streaming ingestion or the Data Management
service, so neither `KustoStreamingIngestClient` nor `QueuedIngestClient` work
against it. We use the universally-supported `.ingest inline` control command
on the engine endpoint instead, which only needs `KustoClient.execute_mgmt`.

Tables must already exist with the right schema — run
`scripts/create_kustainer_tables.py` once before the first ingest.
"""

from __future__ import annotations

import json
import types
import typing
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from sinks.base import Batch, Sink


_PY_TO_KUSTO: dict[Any, str] = {
    str: "string",
    int: "long",
    bool: "bool",
    float: "real",
    datetime: "datetime",
    Any: "dynamic",
}


def kusto_type_for_annotation(annotation: Any) -> str:
    """Map a Pydantic field annotation to a Kusto column type.

    Handles `Optional[T]` / `T | None` by unwrapping the union. Anything that
    isn't a known scalar (dicts, lists, `Any`, custom models, …) maps to
    `dynamic`, which Kusto stores as JSON.
    """
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        non_none = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return kusto_type_for_annotation(non_none[0])
        return "dynamic"
    if annotation is Any:
        return "dynamic"
    return _PY_TO_KUSTO.get(annotation, "dynamic")


def columns_for_model(cls: type[BaseModel]) -> list[tuple[str, str]]:
    """Return `[(column_name, kusto_type), ...]` for a Pydantic model class.

    Column names use field aliases when present (codegen aliases keyword-clash
    field names back to their original Defender column names) so the emitted
    schema matches what `.model_dump(by_alias=True)` produces.
    """
    out: list[tuple[str, str]] = []
    for name, info in cls.model_fields.items():
        column = _column_name(name, info)
        out.append((column, kusto_type_for_annotation(info.annotation)))
    return out


def _column_name(field_name: str, info: FieldInfo) -> str:
    return info.alias or field_name


def _csv_escape(s: str) -> str:
    if any(c in s for c in (",", '"', "\n", "\r")):
        return '"' + s.replace('"', '""') + '"'
    return s


def _format_cell(value: Any, kusto_type: str) -> str:
    if value is None:
        return ""
    if kusto_type == "dynamic":
        return _csv_escape(json.dumps(value, default=str))
    if kusto_type == "bool":
        return "true" if value else "false"
    if kusto_type in ("long", "real"):
        return str(value)
    return _csv_escape(str(value))


def _build_ingest_command(
    table: str,
    events: Iterable[BaseModel],
    columns: list[tuple[str, str]],
) -> str:
    rows: list[str] = []
    for event in events:
        data = event.model_dump(by_alias=True, mode="json")
        cells = [_format_cell(data.get(name), k_type) for name, k_type in columns]
        rows.append(",".join(cells))
    return f".ingest inline into table {table} <|\n" + "\n".join(rows)


def _default_client_factory(cluster_uri: str):
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

    kcsb = KustoConnectionStringBuilder.with_no_authentication(cluster_uri)
    return KustoClient(kcsb)


class KustainerSink:
    def __init__(
        self,
        cluster_uri: str,
        database: str,
        table_prefix: str = "",
        client_factory=_default_client_factory,
    ) -> None:
        """`client_factory(cluster_uri)` is injectable so tests can stub the
        Kusto client without standing up an emulator. In normal use it builds
        a real `KustoClient` against the unauthenticated emulator endpoint."""
        self._database = database
        self._table_prefix = table_prefix
        self._client = client_factory(cluster_uri)
        self._columns_cache: dict[type[BaseModel], list[tuple[str, str]]] = {}

    def _table_for(self, table: str) -> str:
        return f"{self._table_prefix}{table}"

    def _columns_for(self, cls: type[BaseModel]) -> list[tuple[str, str]]:
        cached = self._columns_cache.get(cls)
        if cached is None:
            cached = columns_for_model(cls)
            self._columns_cache[cls] = cached
        return cached

    def write(self, batch: Batch) -> None:
        groups: dict[str, list[BaseModel]] = defaultdict(list)
        for table, event in batch:
            groups[table].append(event)
        for table, events in groups.items():
            columns = self._columns_for(type(events[0]))
            command = _build_ingest_command(self._table_for(table), events, columns)
            self._client.execute_mgmt(self._database, command)

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()


def build(
    cluster_uri: str,
    database: str,
    table_prefix: str = "",
) -> Sink:
    return KustainerSink(
        cluster_uri=cluster_uri,
        database=database,
        table_prefix=table_prefix,
    )
