# XDRGEN

`xdrgen` is a CLI tool that generates production-like Defender XDR telemetry based on a provided YAML profile.

> **⚠️ Experimental / heavily vibe-coded.** The telemetry generated without a very specific profile **will** contain errors — wrong enum values, fields that wouldn't co-occur in real Defender data, distributions that don't match production, etc. Don't rely on it for anything that matters until each table has been evaluated against real-world samples.

Two commands:

1. **`generate`** — produce coherent telemetry events as JSON, driven by an optional YAML profile.
2. **`update-models`** — fetch the canonical Defender XDR / MDE table schemas from [`Azure/Azure-Sentinel`](https://github.com/Azure/Azure-Sentinel) and emit one Pydantic model per table into `./models/`.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (or use `pip install -e .` and drop the `uv run` prefix)

## `generate`

```
░██    ░██ ░███████   ░█████████    ░██████  ░██████████ ░███    ░██
 ░██  ░██  ░██   ░██  ░██     ░██  ░██   ░██ ░██         ░████   ░██
  ░██░██   ░██    ░██ ░██     ░██ ░██        ░██         ░██░██  ░██
   ░███    ░██    ░██ ░█████████  ░██  █████ ░█████████  ░██ ░██ ░██
  ░██░██   ░██    ░██ ░██   ░██   ░██     ██ ░██         ░██  ░██░██
 ░██  ░██  ░██   ░██  ░██    ░██   ░██  ░███ ░██         ░██   ░████
░██    ░██ ░███████   ░██     ░██   ░█████░█ ░██████████ ░██    ░███
                                                               v0.1.0

 Usage: xdrgen generate [OPTIONS] [PROFILE]

 Generate production-like Defender XDR telemetry as JSON.

 Events are buffered in memory and flushed to disk every `--flush-every`
 events — so neither finite (`-n`) nor `--indefinite` runs grow memory
 without bound. The buffer is also flushed on `Ctrl+C` and at the end of
 a finite run, so no event written to memory is ever lost.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   profile      [PROFILE]  Optional YAML profile selecting tables and overriding tenant fixtures.                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --output                  -o      PATH                    Output path. Defaults to `./telemetry.json`, or            │
│                                                           `./telemetry/` with `--per-table`.                         │
│ --count                   -n      INTEGER RANGE [x>=1]    Number of events to generate (ignored with --indefinite).  │
│                                                           [default: 10]                                              │
│ --indefinite                                              Run until interrupted with Ctrl+C.                         │
│ --interval                -i      FLOAT RANGE [x>=0.0]    Seconds to wait between events. [default: 1.0]             │
│ --echo                                                    Also print each event to stdout.                           │
│ --per-table                                               Group events per-table: one file per event (file sink) or  │
│                                                           one topic per table (kafka).                               │
│ --flush-every                     INTEGER RANGE [x>=1]    Buffer this many events before flushing to the active      │
│                                                           sink.                                                      │
│                                                           [default: 10000]                                           │
│ --sink                            [json|kafka|kustainer]  Destination for events: `json`, `kafka`, or `kustainer`.   │
│                                                           [default: json]                                            │
│ --kafka-bootstrap                 TEXT                    Kafka bootstrap servers, e.g. `localhost:9092`. Required   │
│                                                           for --sink kafka.                                          │
│ --kafka-topic                     TEXT                    Kafka topic to produce to (ignored with --per-table).      │
│                                                           [default: xdrgen]                                          │
│ --kafka-topic-prefix              TEXT                    Prefix for per-table Kafka topic names (only with          │
│                                                           --per-table).                                              │
│                                                           [default: xdrgen.]                                         │
│ --kustainer-cluster               TEXT                    Kustainer (Kusto emulator) HTTP endpoint.                  │
│                                                           [default: http://localhost:8080]                           │
│ --kustainer-database              TEXT                    Kustainer database events are ingested into.               │
│                                                           [default: NetDefaultDB]                                    │
│ --kustainer-table-prefix          TEXT                    Prefix prepended to every Kustainer table name.            │
│ --help                                                    Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Each event is validated through its Pydantic model (so field names and types match real Defender XDR columns) and handed to a *sink* — `json` by default.

```bash
# All tables that have a generator, default file sink → ./telemetry.json
uv run xdrgen generate

# 100 events, no delay, into a custom file
uv run xdrgen generate -n 100 -i 0 -o ./out/cae.json

# One JSON file per event
uv run xdrgen generate -n 100 -o ./out/events --per-table

# Stream forever, flush every 100 events
uv run xdrgen generate --indefinite --flush-every 100

# Stream to Kafka
uv run xdrgen generate --sink kafka --kafka-bootstrap localhost:9092
```

`--per-table` cross-cuts whichever sink is active — it changes how events are *grouped*, not where they go. For `json` it becomes one file per event under `./telemetry/`; for `kafka` it becomes one topic per table (`{--kafka-topic-prefix}{TableName}`).

### Profile

The YAML profile is optional. Without one, every table that has a generator is emitted using the default `contoso.com` tenant fixture. With one, you can select a subset of tables and/or override fixtures (tenant id, domain, users, devices, IPs, user agents, conditional access policies, Graph API endpoint catalogue, Graph API regions, email templates, …) so the stream looks like it came from *your* tenant.

A fully documented example is shipped at [`profile.example.yaml`](./profile.example.yaml) — copy it and edit:

```bash
cp profile.example.yaml profile.yaml
uv run xdrgen generate profile.yaml -n 100
```

The profile is validated by Pydantic models in [`world.py`](./world.py); unknown keys, wrong shapes, and missing required sub-fields fail fast.

#### Threat profiles

Ready-made profiles that shape the output stream like a specific attack technique live in [`examples/threat-profiles/`](./examples/threat-profiles/):

- [`azure-hound/`](./examples/threat-profiles/azure-hound/) — emits the 14 Microsoft Graph endpoints AzureHound walks during directory collection, sized to trip the [CloudBrothers GraphAPIAuditEvents detection](https://cloudbrothers.info/detect-threats-graphapiauditevents-part-3/).

### Sinks

Sinks live in [`sinks/`](./sinks/). Three ship today:

- **`json`** _(default)_ — JSON to disk. See `sinks/json.py`.
- **`kafka`** — produces JSON to a Kafka broker via `kafka-python`. See `sinks/kafka.py`.
- **`kustainer`** — ingests directly into [Kustainer](https://learn.microsoft.com/en-us/azure/data-explorer/kusto-emulator-overview), Microsoft's official Kusto/ADX emulator, using `.ingest inline`. See `sinks/kustainer.py`.

Compose files for local Kafka and Kustainer are under [`docker/`](./docker/). The Kustainer compose file ships a `kustainer-init` sidecar that waits for the emulator and runs [`scripts/create_kustainer_tables.py`](./scripts/create_kustainer_tables.py) and [`scripts/create_kustainer_functions.py`](./scripts/create_kustainer_functions.py) automatically — re-runs are safe (`.create-merge` / `.create-or-alter`):

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d
uv run xdrgen generate -n 100 -i 0 --sink kustainer
```

#### Kustainer Frontend

For an in-browser KQL editor that queries the local Kustainer instance (Monaco-Kusto + AG Grid), see [`examples/kustainer-frontend/`](./examples/kustainer-frontend/). The kustainer compose file ships a `frontend` service that builds and serves the bundle behind nginx on http://localhost:5173 — no `npm install` needed.

### Supported tables

Handcrafted generators currently exist for: `CloudAppEvents`, `DeviceEvents`, `DeviceFileCertificateInfo`, `DeviceImageLoadEvents`, `DeviceLogonEvents`, `DeviceNetworkEvents`, `DeviceNetworkInfo`, `DeviceProcessEvents`, `DeviceRegistryEvents`, `EmailAttachmentInfo`, `EmailEvents`, `EmailPostDeliveryEvents`, `EmailUrlInfo`, `EntraIdSignInEvents`, `EntraIdSpnSignInEvents`, `GraphApiAuditEvents`, `IdentityAccountInfo`, `IdentityDirectoryEvents`, `IdentityEvents`, `IdentityLogonEvents`, `IdentityQueryEvents`, `UrlClickEvents`.

Per-table specifics live in [`generators/PRODUCTION_LIKE_DATA.md`](./generators/PRODUCTION_LIKE_DATA.md). Listing an unsupported table in a profile fails fast with the available list.

## `update-models`

Fetches the table catalogue and column schemas from `Azure/Azure-Sentinel/Tools/Solutions Analyzer/`, filters to rows whose `category` contains `xdr` or `mde`, and writes one Pydantic model per table into `./models/`.

```bash
uv run xdrgen update-models
```

All fields are `Optional[T] = Field(None, ...)` because XDR events are inherently sparse. You usually don't need to run this yourself — a [daily GitHub Actions workflow](./.github/workflows/update-models.yml) opens a PR with any schema drift, so `main` tracks upstream.

## Development

```bash
uv run ruff format .       # format
uv run ruff check --fix .  # lint
uv run pytest -q           # test
```

To add a new sink: drop a module in `sinks/` implementing the `Sink` protocol from `sinks/base.py` plus a `build(...)` factory, add an entry to `SinkChoice` and a branch in `_build_sink` in `main.py`, and add a unit test in `tests/test_sinks.py`.
