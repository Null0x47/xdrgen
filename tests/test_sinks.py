from __future__ import annotations

import csv
import json
import pathlib
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from sinks import csv as csv_sink
from sinks import json as json_sink
from sinks import kafka as kafka_sink
from sinks import kustainer as kustainer_sink


class _StubEvent:
    """BaseModel stand-in — sinks only call `.model_dump_json()`."""

    def __init__(self, name: str) -> None:
        self._name = name

    def model_dump_json(self, by_alias: bool = False, indent: int | None = None) -> str:
        return json.dumps({"table": self._name}, indent=indent)


class _RecordingProducer:
    """KafkaProducer stand-in covering the methods KafkaSink calls."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.sent: list[dict] = []
        self.flushed = 0
        self.closed = False

    def send(self, topic, key=None, value=None):
        self.sent.append({"topic": topic, "key": key, "value": value})

    def flush(self):
        self.flushed += 1

    def close(self):
        self.closed = True


def _build_kafka_sink(per_table: bool, topic_prefix: str = "") -> tuple:
    producer = _RecordingProducer()
    sink = kafka_sink.KafkaSink(
        bootstrap_servers="broker-1:9092,broker-2:9092",
        per_table=per_table,
        topic="xdrgen",
        topic_prefix=topic_prefix,
        producer_factory=lambda **kw: producer.kwargs.update(kw) or producer,
    )
    return sink, producer


def test_kafka_sink_single_topic_routes_every_event_to_one_topic():
    sink, producer = _build_kafka_sink(per_table=False)

    sink.write(
        [
            ("CloudAppEvents", _StubEvent("CloudAppEvents")),
            ("EmailEvents", _StubEvent("EmailEvents")),
        ]
    )

    assert {m["topic"] for m in producer.sent} == {"xdrgen"}
    assert len(producer.sent) == 2


def test_kafka_sink_per_table_routes_each_event_to_its_own_topic():
    sink, producer = _build_kafka_sink(per_table=True)

    sink.write(
        [
            ("CloudAppEvents", _StubEvent("CloudAppEvents")),
            ("EmailEvents", _StubEvent("EmailEvents")),
            ("CloudAppEvents", _StubEvent("CloudAppEvents")),
        ]
    )

    topics = [m["topic"] for m in producer.sent]
    assert topics == ["CloudAppEvents", "EmailEvents", "CloudAppEvents"]


def test_kafka_sink_per_table_topic_prefix_is_applied():
    sink, producer = _build_kafka_sink(per_table=True, topic_prefix="xdrgen.")

    sink.write([("CloudAppEvents", _StubEvent("CloudAppEvents"))])

    assert producer.sent[0]["topic"] == "xdrgen.CloudAppEvents"


def test_kafka_sink_message_key_is_table_name_and_value_is_event_json():
    sink, producer = _build_kafka_sink(per_table=False)

    sink.write([("CloudAppEvents", _StubEvent("CloudAppEvents"))])

    msg = producer.sent[0]
    assert msg["key"] == "CloudAppEvents"
    assert json.loads(msg["value"]) == {"table": "CloudAppEvents"}


def test_kafka_sink_splits_bootstrap_servers_on_comma():
    sink, producer = _build_kafka_sink(per_table=False)
    assert sink
    assert producer.kwargs["bootstrap_servers"] == ["broker-1:9092", "broker-2:9092"]


def test_kafka_sink_close_flushes_and_closes_producer():
    sink, producer = _build_kafka_sink(per_table=False)
    sink.close()
    assert producer.flushed >= 1
    assert producer.closed is True


class _SampleEvent(BaseModel):
    """Exercises every Kusto type the sink emits."""

    Name: Optional[str] = Field(None)
    Count: Optional[int] = Field(None)
    Score: Optional[float] = Field(None)
    Active: Optional[bool] = Field(None)
    Timestamp: Optional[datetime] = Field(None)
    Payload: Optional[Any] = Field(None)
    Kind: Optional[str] = Field(None, alias="type")


class _RecordingKustoClient:
    """KustoClient stand-in for KustainerSink tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    def execute_mgmt(self, database: str, command: str):
        self.calls.append((database, command))

    def close(self) -> None:
        self.closed = True


def _build_kustainer_sink(table_prefix: str = "") -> tuple:
    client = _RecordingKustoClient()
    sink = kustainer_sink.KustainerSink(
        cluster_uri="http://localhost:8080",
        database="NetDefaultDB",
        table_prefix=table_prefix,
        client_factory=lambda _uri: client,
    )
    return sink, client


def test_kustainer_sink_groups_events_by_table_into_one_command_per_table():
    sink, client = _build_kustainer_sink()

    sink.write(
        [
            ("SampleA", _SampleEvent(Name="a")),
            ("SampleB", _SampleEvent(Name="b")),
            ("SampleA", _SampleEvent(Name="c")),
        ]
    )

    assert len(client.calls) == 2
    targets = [cmd.splitlines()[0] for _db, cmd in client.calls]
    assert ".ingest inline into table SampleA <|" in targets
    assert ".ingest inline into table SampleB <|" in targets


def test_kustainer_sink_table_prefix_is_applied():
    sink, client = _build_kustainer_sink(table_prefix="xdr_")

    sink.write([("SampleA", _SampleEvent(Name="a"))])

    assert client.calls[0][1].startswith(".ingest inline into table xdr_SampleA <|")


def test_kustainer_sink_serialises_each_kusto_type_correctly():
    sink, client = _build_kustainer_sink()

    sink.write(
        [
            (
                "Sample",
                _SampleEvent(
                    Name="hello, world",
                    Count=42,
                    Score=3.5,
                    Active=True,
                    Timestamp=datetime(2024, 1, 2, 3, 4, 5),
                    Payload={"k": "v"},
                    type="alpha",
                ),
            )
        ]
    )

    _, command = client.calls[0]
    row = command.splitlines()[1]
    cells = list(_iter_csv_cells(row))
    assert cells[0] == '"hello, world"'
    assert cells[1] == "42"
    assert cells[2] == "3.5"
    assert cells[3] == "true"
    assert cells[4] == "2024-01-02T03:04:05"
    assert cells[5] == '"{""k"": ""v""}"'
    assert cells[6] == "alpha"


def test_kustainer_sink_emits_empty_cell_for_none_values():
    sink, client = _build_kustainer_sink()

    sink.write([("Sample", _SampleEvent())])

    _, command = client.calls[0]
    row = command.splitlines()[1]
    assert row == ",,,,,,"


def test_kustainer_sink_close_closes_underlying_client():
    sink, client = _build_kustainer_sink()
    sink.close()
    assert client.closed is True


def test_kustainer_columns_for_model_maps_pydantic_types_to_kusto_types():
    columns = dict(kustainer_sink.columns_for_model(_SampleEvent))

    assert columns == {
        "Name": "string",
        "Count": "long",
        "Score": "real",
        "Active": "bool",
        "Timestamp": "datetime",
        "Payload": "dynamic",
        "type": "string",
    }


def _iter_csv_cells(row: str):
    """CSV splitter for the test — handles `""` escapes."""
    cell: list[str] = []
    in_quotes = False
    i = 0
    while i < len(row):
        c = row[i]
        if in_quotes:
            if c == '"' and i + 1 < len(row) and row[i + 1] == '"':
                cell.append('""')
                i += 2
                continue
            if c == '"':
                in_quotes = False
                cell.append(c)
                i += 1
                continue
            cell.append(c)
            i += 1
            continue
        if c == '"':
            in_quotes = True
            cell.append(c)
            i += 1
            continue
        if c == ",":
            yield "".join(cell)
            cell = []
            i += 1
            continue
        cell.append(c)
        i += 1
    yield "".join(cell)


def test_json_sink_build_picks_per_table_when_flag_set(tmp_path: pathlib.Path):
    out_dir = tmp_path / "out"
    sink = json_sink.build(out_dir, per_table=True)
    assert isinstance(sink, json_sink.PerTableJsonSink)
    sink.close()


def test_json_sink_build_picks_json_array_by_default(tmp_path: pathlib.Path):
    out_file = tmp_path / "out.json"
    sink = json_sink.build(out_file, per_table=False)
    assert isinstance(sink, json_sink.JsonArraySink)
    sink.close()


def test_csv_sink_build_picks_per_table_when_flag_set(tmp_path: pathlib.Path):
    out_dir = tmp_path / "out"
    sink = csv_sink.build(out_dir, per_table=True)
    assert isinstance(sink, csv_sink.PerTableCsvSink)
    sink.close()


def test_csv_sink_build_picks_single_file_by_default(tmp_path: pathlib.Path):
    out_file = tmp_path / "out.csv"
    sink = csv_sink.build(out_file, per_table=False)
    assert isinstance(sink, csv_sink.CsvSingleFileSink)
    sink.close()


def test_csv_single_file_sink_writes_header_and_one_row_per_event(
    tmp_path: pathlib.Path,
):
    out_file = tmp_path / "out.csv"
    sink = csv_sink.CsvSingleFileSink(out_file)
    sink.write(
        [
            ("CloudAppEvents", _StubEvent("CloudAppEvents")),
            ("EmailEvents", _StubEvent("EmailEvents")),
        ]
    )
    sink.close()

    rows = list(csv.reader(out_file.open("r", encoding="utf-8")))
    assert rows[0] == ["_table", "event_json"]
    assert rows[1] == ["CloudAppEvents", '{"table": "CloudAppEvents"}']
    assert rows[2] == ["EmailEvents", '{"table": "EmailEvents"}']


def test_per_table_csv_sink_writes_one_file_per_event_with_model_columns(
    tmp_path: pathlib.Path,
):
    sink = csv_sink.PerTableCsvSink(tmp_path)
    sink.write(
        [
            (
                "Sample",
                _SampleEvent(
                    Name="hello, world",
                    Count=42,
                    Score=3.5,
                    Active=True,
                    Timestamp=datetime(2024, 1, 2, 3, 4, 5),
                    Payload={"k": "v"},
                    type="alpha",
                ),
            ),
            ("Sample", _SampleEvent(Name="second")),
        ]
    )
    sink.close()

    first = list(csv.reader((tmp_path / "Sample-0000.csv").open("r", encoding="utf-8")))
    assert first[0] == [
        "Name",
        "Count",
        "Score",
        "Active",
        "Timestamp",
        "Payload",
        "type",
    ]
    assert first[1] == [
        "hello, world",
        "42",
        "3.5",
        "true",
        "2024-01-02T03:04:05",
        '{"k": "v"}',
        "alpha",
    ]

    second = list(
        csv.reader((tmp_path / "Sample-0001.csv").open("r", encoding="utf-8"))
    )
    assert second[1] == ["second", "", "", "", "", "", ""]


def test_per_table_csv_sink_counter_is_per_table(tmp_path: pathlib.Path):
    sink = csv_sink.PerTableCsvSink(tmp_path)
    sink.write(
        [
            ("SampleA", _SampleEvent(Name="a")),
            ("SampleB", _SampleEvent(Name="b")),
            ("SampleA", _SampleEvent(Name="c")),
        ]
    )
    sink.close()

    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["SampleA-0000.csv", "SampleA-0001.csv", "SampleB-0000.csv"]
