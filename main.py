from __future__ import annotations

import asyncio
import enum
import importlib.metadata
import pathlib
import random
import time

import typer
import yaml

from pydantic import BaseModel, ValidationError

from fetcher import fetch_schema_sources
from model_codegen import generate_init_file, generate_model_file
from parser import parse_xdr_table_names, parse_xdr_tables

try:
    from generators import GENERATORS
except ImportError:
    # Models not generated yet; `generate` will fail loudly via _load_profile.
    GENERATORS: dict = {}

from sinks import Sink
from sinks import csv as csv_sink
from sinks import json as json_sink
from sinks import kafka as kafka_sink
from sinks import kustainer as kustainer_sink
from world import Profile


class SinkChoice(str, enum.Enum):
    json = "json"
    csv = "csv"
    kafka = "kafka"
    kustainer = "kustainer"


MODELS_DIR = pathlib.Path("./models")

_BANNER = r"""
░██    ░██ ░███████   ░█████████    ░██████  ░██████████ ░███    ░██ 
 ░██  ░██  ░██   ░██  ░██     ░██  ░██   ░██ ░██         ░████   ░██ 
  ░██░██   ░██    ░██ ░██     ░██ ░██        ░██         ░██░██  ░██ 
   ░███    ░██    ░██ ░█████████  ░██  █████ ░█████████  ░██ ░██ ░██ 
  ░██░██   ░██    ░██ ░██   ░██   ░██     ██ ░██         ░██  ░██░██ 
 ░██  ░██  ░██   ░██  ░██    ░██   ░██  ░███ ░██         ░██   ░████ 
░██    ░██ ░███████   ░██     ░██   ░█████░█ ░██████████ ░██    ░███
""".lstrip("\n")


def _get_version() -> str:
    try:
        return importlib.metadata.version("xdrgen")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _print_banner() -> None:
    width = max(len(line) for line in _BANNER.splitlines())
    version_line = f"v{_get_version()}".rjust(width)
    typer.echo(_BANNER + version_line + "\n", err=True)


app = typer.Typer(
    help="Generate Pydantic models and production-like telemetry for Defender XDR tables.",
    no_args_is_help=True,
)


@app.callback()
def callback() -> None:
    _print_banner()


async def _update_models() -> None:
    typer.echo("Fetching schema sources from Azure-Sentinel...")
    reference_csvs, schemas_csv = await fetch_schema_sources()

    xdr_names = parse_xdr_table_names(reference_csvs)
    typer.echo(f"Found {len(xdr_names)} Defender XDR tables.")

    tables = parse_xdr_tables(schemas_csv, xdr_names)

    missing = xdr_names - {t.model_name for t in tables}
    for name in sorted(missing):
        typer.echo(f"WARNING: no schema rows for XDR table {name}", err=True)

    MODELS_DIR.mkdir(exist_ok=True)

    written: list = []
    for table in tables:
        if not table.columns:
            typer.echo(f"WARNING: no columns parsed for {table.model_name}", err=True)
            continue
        filename, content = generate_model_file(table)
        (MODELS_DIR / filename).write_text(content, encoding="utf-8")
        written.append(table)

    init_content = generate_init_file(written)
    (MODELS_DIR / "__init__.py").write_text(init_content, encoding="utf-8")
    typer.echo(f"Done. {len(written)} models written to {MODELS_DIR}/")


@app.command("update-models")
def update_models() -> None:
    """Fetch the latest Defender XDR table definitions and regenerate Pydantic models in ./models/."""
    asyncio.run(_update_models())


def _load_profile(profile: pathlib.Path) -> Profile:
    """Parse + validate a YAML profile; reports errors via typer.BadParameter."""
    raw = yaml.safe_load(profile.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise typer.BadParameter(f"{profile} must contain a top-level YAML mapping.")

    try:
        parsed = Profile.model_validate(raw)
    except ValidationError as exc:
        raise typer.BadParameter(f"{profile}: {exc}") from exc

    unknown = [t for t in (parsed.tables or []) if t not in GENERATORS]
    if unknown:
        available = ", ".join(sorted(GENERATORS)) or "(none yet)"
        raise typer.BadParameter(
            f"No generator for: {', '.join(unknown)}. Available: {available}"
        )
    return parsed


FLUSH_EVERY = 10_000


def _build_sink(
    sink_choice: SinkChoice,
    output: pathlib.Path,
    *,
    per_table: bool,
    kafka_bootstrap: str | None,
    kafka_topic: str,
    kafka_topic_prefix: str,
    kustainer_cluster: str,
    kustainer_database: str,
    kustainer_table_prefix: str,
) -> Sink:
    """Build the active sink for `--sink`."""
    if sink_choice is SinkChoice.json:
        return json_sink.build(output, per_table=per_table)
    if sink_choice is SinkChoice.csv:
        return csv_sink.build(output, per_table=per_table)
    if sink_choice is SinkChoice.kafka:
        if not kafka_bootstrap:
            raise typer.BadParameter(
                "--kafka-bootstrap is required when --sink kafka is chosen."
            )
        return kafka_sink.build(
            bootstrap_servers=kafka_bootstrap,
            per_table=per_table,
            topic=kafka_topic,
            topic_prefix=kafka_topic_prefix,
        )
    if sink_choice is SinkChoice.kustainer:
        return kustainer_sink.build(
            cluster_uri=kustainer_cluster,
            database=kustainer_database,
            table_prefix=kustainer_table_prefix,
        )
    raise typer.BadParameter(f"Unknown sink: {sink_choice}")


@app.command("generate")
def generate(
    profile: pathlib.Path | None = typer.Argument(
        None,
        exists=True,
        readable=True,
        help="Optional YAML profile selecting tables and overriding tenant fixtures.",
    ),
    output: pathlib.Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path. Defaults to `./telemetry.json`, or `./telemetry/` with `--per-table`.",
    ),
    count: int = typer.Option(
        10,
        "--count",
        "-n",
        min=1,
        help="Number of events to generate (ignored with --indefinite).",
    ),
    indefinite: bool = typer.Option(
        False,
        "--indefinite",
        help="Run until interrupted with Ctrl+C.",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        "-i",
        min=0.0,
        help="Seconds to wait between events.",
    ),
    echo: bool = typer.Option(
        False,
        "--echo",
        help="Also print each event to stdout.",
    ),
    per_table: bool = typer.Option(
        False,
        "--per-table",
        help="Group events per-table: one file per event (file sink) or one topic per table (kafka).",
    ),
    flush_every: int = typer.Option(
        FLUSH_EVERY,
        "--flush-every",
        min=1,
        help="Buffer this many events before flushing to the active sink.",
    ),
    sink: SinkChoice = typer.Option(
        SinkChoice.json,
        "--sink",
        help="Destination for events: `json`, `csv`, `kafka`, or `kustainer`.",
    ),
    kafka_bootstrap: str | None = typer.Option(
        None,
        "--kafka-bootstrap",
        help="Kafka bootstrap servers, e.g. `localhost:9092`. Required for --sink kafka.",
    ),
    kafka_topic: str = typer.Option(
        "xdrgen",
        "--kafka-topic",
        help="Kafka topic to produce to (ignored with --per-table).",
    ),
    kafka_topic_prefix: str = typer.Option(
        "xdrgen.",
        "--kafka-topic-prefix",
        help="Prefix for per-table Kafka topic names (only with --per-table).",
    ),
    kustainer_cluster: str = typer.Option(
        "http://localhost:8080",
        "--kustainer-cluster",
        help="Kustainer (Kusto emulator) HTTP endpoint.",
    ),
    kustainer_database: str = typer.Option(
        "NetDefaultDB",
        "--kustainer-database",
        help="Kustainer database events are ingested into.",
    ),
    kustainer_table_prefix: str = typer.Option(
        "",
        "--kustainer-table-prefix",
        help="Prefix prepended to every Kustainer table name.",
    ),
) -> None:
    """Generate production-like Defender XDR telemetry as JSON.

    Events are buffered and flushed every --flush-every, on Ctrl+C, and at
    end-of-run, so memory stays bounded and no event is lost.
    """
    prof = _load_profile(profile) if profile is not None else Profile()
    tables = prof.tables or sorted(GENERATORS)
    world = prof.build_world()

    if output is None:
        if per_table:
            output = pathlib.Path("./telemetry")
        elif sink is SinkChoice.csv:
            output = pathlib.Path("./telemetry.csv")
        else:
            output = pathlib.Path("./telemetry.json")

    mode = "indefinite" if indefinite else f"{count} event(s)"
    typer.echo(f"Generating {mode} (tables={tables}, interval={interval}s)")

    active_sink = _build_sink(
        sink,
        output,
        per_table=per_table,
        kafka_bootstrap=kafka_bootstrap,
        kafka_topic=kafka_topic,
        kafka_topic_prefix=kafka_topic_prefix,
        kustainer_cluster=kustainer_cluster,
        kustainer_database=kustainer_database,
        kustainer_table_prefix=kustainer_table_prefix,
    )
    buffer: list[tuple[str, BaseModel]] = []
    total = 0
    try:
        try:
            while indefinite or total < count:
                if total > 0 and interval > 0:
                    time.sleep(interval)
                table = random.choice(tables)
                event = GENERATORS[table](world)
                buffer.append((table, event))
                total += 1
                if echo:
                    typer.echo(event.model_dump_json(by_alias=True))
                if len(buffer) >= flush_every:
                    active_sink.write(buffer)
                    buffer.clear()
        except KeyboardInterrupt:
            typer.echo(f"\nInterrupted after {total} event(s).")
    finally:
        if buffer:
            active_sink.write(buffer)
        active_sink.close()

    if sink is SinkChoice.json or sink is SinkChoice.csv:
        destination = str(output)
    elif sink is SinkChoice.kafka:
        destination = f"kafka://{kafka_bootstrap}"
    else:
        destination = f"kustainer://{kustainer_cluster}/{kustainer_database}"
    typer.echo(f"Wrote {total} event(s) to {destination}.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
