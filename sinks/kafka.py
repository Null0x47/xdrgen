"""Kafka sink.

Each event is serialised as JSON (matching the file sink's wire format) and
produced via `kafka-python`. The table name is used as the message key so
partitioning stays consistent per table, and `--per-table` flips routing
from one shared topic to one topic per table named `{prefix}{TableName}`.

`build()` is the public entry point — `main.py` wires it into a `MultiSink`
when `--kafka-bootstrap` is set.
"""

from __future__ import annotations

from kafka import KafkaProducer

from sinks.base import Batch, Sink


class KafkaSink:
    def __init__(
        self,
        bootstrap_servers: str,
        per_table: bool,
        topic: str,
        topic_prefix: str,
        producer_factory=KafkaProducer,
    ) -> None:
        """`producer_factory` is injectable so tests can stub the producer
        without standing up a broker. In normal use it's the real
        `KafkaProducer` constructor."""
        self._producer = producer_factory(
            bootstrap_servers=[s.strip() for s in bootstrap_servers.split(",")],
            value_serializer=lambda v: v.encode("utf-8"),
            key_serializer=lambda v: v.encode("utf-8") if v is not None else None,
        )
        self._per_table = per_table
        self._topic = topic
        self._topic_prefix = topic_prefix

    def _topic_for(self, table: str) -> str:
        return f"{self._topic_prefix}{table}" if self._per_table else self._topic

    def write(self, batch: Batch) -> None:
        for table, event in batch:
            self._producer.send(
                self._topic_for(table),
                key=table,
                value=event.model_dump_json(by_alias=True),
            )
        self._producer.flush()

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()


def build(
    bootstrap_servers: str,
    per_table: bool,
    topic: str,
    topic_prefix: str,
) -> Sink:
    return KafkaSink(
        bootstrap_servers=bootstrap_servers,
        per_table=per_table,
        topic=topic,
        topic_prefix=topic_prefix,
    )
