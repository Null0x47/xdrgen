from __future__ import annotations

import json
import pathlib

from sinks import file as file_sink
from sinks import kafka as kafka_sink


class _StubEvent:
    """Minimal BaseModel-shaped object — sinks call `.model_dump_json()`."""

    def __init__(self, name: str) -> None:
        self._name = name

    def model_dump_json(self, by_alias: bool = False, indent: int | None = None) -> str:
        return json.dumps({"table": self._name}, indent=indent)


class _RecordingProducer:
    """Stand-in for `kafka.KafkaProducer` so KafkaSink tests don't need a
    broker. Only exercises the methods KafkaSink actually calls."""

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
    assert sink  # silence unused warning — fixture call already populated kwargs
    assert producer.kwargs["bootstrap_servers"] == ["broker-1:9092", "broker-2:9092"]


def test_kafka_sink_close_flushes_and_closes_producer():
    sink, producer = _build_kafka_sink(per_table=False)
    sink.close()
    assert producer.flushed >= 1
    assert producer.closed is True


def test_file_sink_build_picks_per_table_when_flag_set(tmp_path: pathlib.Path):
    out_dir = tmp_path / "out"
    sink = file_sink.build(out_dir, per_table=True)
    assert isinstance(sink, file_sink.PerTableFileSink)
    sink.close()


def test_file_sink_build_picks_json_array_by_default(tmp_path: pathlib.Path):
    out_file = tmp_path / "out.json"
    sink = file_sink.build(out_file, per_table=False)
    assert isinstance(sink, file_sink.JsonArrayFileSink)
    sink.close()
