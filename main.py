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
from generators import GENERATORS
from sinks import Sink
from sinks import file as file_sink
from sinks import kafka as kafka_sink
from world import Profile


class SinkChoice(str, enum.Enum):
    file = "file"
    kafka = "kafka"


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
    """Parse and validate the YAML profile into a `world.Profile`.

    Validation errors (unknown keys, wrong shapes, bad types) surface as
    `typer.BadParameter` so the CLI reports them cleanly rather than dumping
    a Pydantic stack trace.
    """
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
) -> Sink:
    """Build the single active sink based on the `--sink` flag.

    Adding a new sink is a one-file change in `sinks/` plus a new branch and
    `SinkChoice` enum value here.
    """
    if sink_choice is SinkChoice.file:
        return file_sink.build(output, per_table=per_table)
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
    raise typer.BadParameter(f"Unknown sink: {sink_choice}")


@app.command("generate")
def generate(
    profile: pathlib.Path | None = typer.Argument(
        None,
        exists=True,
        readable=True,
        help=(
            "Optional YAML profile: `tables:` picks which tables to emit, "
            "`overrides:` replaces the default tenant fixtures. Omit to emit "
            "every registered table with `contoso.com` defaults. "
            "See `xdrgen.example.yaml`."
        ),
    ),
    output: pathlib.Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help=(
            "Where to write the result. Defaults to `./telemetry.json` "
            "(a single JSON array of events). When `--per-table` is set, the "
            "default flips to `./telemetry/` (a directory of per-event files)."
        ),
    ),
    count: int = typer.Option(
        10,
        "--count",
        "-n",
        min=1,
        help="Number of events to generate. Ignored when --indefinite is set.",
    ),
    indefinite: bool = typer.Option(
        False,
        "--indefinite",
        help="Generate events forever until interrupted (Ctrl+C).",
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
        help="Also print every generated event to stdout as it is generated.",
    ),
    per_table: bool = typer.Option(
        False,
        "--per-table",
        help=(
            "Write each event to its own JSON file named "
            "`{TableName}-{n}.json` inside the output directory, instead of "
            "one combined JSON array."
        ),
    ),
    flush_every: int = typer.Option(
        FLUSH_EVERY,
        "--flush-every",
        min=1,
        help=(
            "Buffer this many events in memory before flushing them to disk. "
            "Lower values trade throughput for tighter memory use; higher "
            "values batch more aggressively. The buffer is also flushed at "
            "the end of a run and on Ctrl+C, so events are never lost."
        ),
    ),
    sink: SinkChoice = typer.Option(
        SinkChoice.file,
        "--sink",
        help=(
            "Where to send generated events. `file` writes JSON to disk; "
            "`kafka` produces to a broker (requires --kafka-bootstrap)."
        ),
    ),
    kafka_bootstrap: str | None = typer.Option(
        None,
        "--kafka-bootstrap",
        help=(
            "Comma-separated Kafka bootstrap servers (e.g. `localhost:9092`). "
            "Required when --sink is `kafka`."
        ),
    ),
    kafka_topic: str = typer.Option(
        "xdrgen",
        "--kafka-topic",
        help=(
            "Kafka topic to produce events to. Ignored when `--per-table` is "
            "set, which routes each event to a topic named after its table."
        ),
    ),
    kafka_topic_prefix: str = typer.Option(
        "xdrgen.",
        "--kafka-topic-prefix",
        help=(
            "Prefix prepended to per-table Kafka topic names (used only with "
            "`--per-table`). Default `xdrgen.` → `xdrgen.CloudAppEvents`. "
            "Pass an empty string to use the bare table name."
        ),
    ),
) -> None:
    """Generate production-like Defender XDR telemetry as JSON.

    Events are buffered in memory and flushed to disk every `--flush-every`
    events — so neither finite (`-n`) nor `--indefinite` runs grow memory
    without bound. The buffer is also flushed on `Ctrl+C` and at the end of
    a finite run, so no event written to memory is ever lost.
    """
    prof = _load_profile(profile) if profile is not None else Profile()
    tables = prof.tables or sorted(GENERATORS)
    world = prof.build_world()

    if output is None:
        output = (
            pathlib.Path("./telemetry")
            if per_table
            else pathlib.Path("./telemetry.json")
        )

    mode = "indefinite" if indefinite else f"{count} event(s)"
    typer.echo(f"Generating {mode} (tables={tables}, interval={interval}s)")

    active_sink = _build_sink(
        sink,
        output,
        per_table=per_table,
        kafka_bootstrap=kafka_bootstrap,
        kafka_topic=kafka_topic,
        kafka_topic_prefix=kafka_topic_prefix,
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

    destination = (
        str(output) if sink is SinkChoice.file else f"kafka://{kafka_bootstrap}"
    )
    typer.echo(f"Wrote {total} event(s) to {destination}.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
