# XDRGEN

`xdrgen` is a CLI tool that generates production-like Defender XDR telemetry based on a provided YAML profile.

> **⚠️ Experimental / heavily vibe-coded.** This project is a work in progress and was largely built by feel rather than against an authoritative spec. The generated telemetry **will** contain errors — wrong enum values, fields that wouldn't co-occur in real Defender data, distributions that don't match production, etc. Don't rely on it for anything that matters until each table has been evaluated against real-world samples. Correctness will be tightened in future changes.

It does two things:

1. **`generate`** — produce coherent, production-like telemetry events as JSON, driven by a YAML profile that lists which tables to emit.
2. **`update-models`** — fetch the canonical list of Defender XDR / MDE tables and their Solution Analyzer column schemas from the [`Azure/Azure-Sentinel`](https://github.com/Azure/Azure-Sentinel) repo, and emit one strongly-typed Pydantic model per table into `./models/`.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
uv sync
```

## Commands

### `generate`

Produce coherent, production-like telemetry events as JSON, driven by an optional YAML profile. Each event is generated, validated through its Pydantic model (so field names and types match the real Defender XDR columns), and handed to a *sink* — `file` by default, `kafka` for streaming to a broker. Pick one with `--sink`; see [Sinks](#sinks) below for what ships and how to add more.

Events are buffered in memory and flushed to the active sink every `--flush-every` events (default 10 000), as well as at the end of a run and on `Ctrl+C`. Neither finite (`-n`) nor `--indefinite` runs grow memory without bound, and no buffered event is ever lost.

`--per-table` cross-cuts whichever sink is active — it changes how events are *grouped*, not where they're sent:

- `--sink file` (default): one combined `./telemetry.json` array → with `--per-table`, one file per event under `./telemetry/{TableName}-{n:04d}.json`.
- `--sink kafka`: every event to `--kafka-topic` (default `xdrgen`) → with `--per-table`, one topic per table named `{--kafka-topic-prefix}{TableName}` (default prefix `xdrgen.` → `xdrgen.CloudAppEvents`, `xdrgen.EmailEvents`, …).

Both the YAML profile itself and its `tables:` key are optional — omit either to generate for every table that has a generator.

```bash
# All tables that have a generator, file sink, ./telemetry.json
uv run xdrgen generate

# Pass a profile to override defaults and/or restrict to a subset of tables
uv run xdrgen generate xdrgen.yaml

# Stream to Kafka instead, single topic
uv run xdrgen generate xdrgen.yaml --sink kafka --kafka-bootstrap localhost:9092
```

```yaml
# xdrgen.yaml — `tables:` optional; omit to include every registered table
tables:
  - CloudAppEvents
```

Pass `--echo` to also stream every generated event to stdout as it is written, regardless of which sink is active — useful for piping or watching the stream live.

#### Profile overrides

The same YAML profile can carry an optional `overrides:` mapping to replace fixtures baked into the default `World`. Useful when you want the stream to look like it came from *your* tenant rather than the default `contoso.com` fixture. Every override key is optional; omit the whole block (or individual keys) to keep the defaults.

The profile is validated by Pydantic models defined in [`world.py`](./world.py) (`Profile`, `Overrides`, plus the typed sub-models for `User`, `IPEntry`, `ClientApp`, etc.) — unknown keys, wrong shapes, and missing required sub-fields fail fast with a clear error from `xdrgen generate`. At runtime, `Profile.build_world()` produces a frozen `World` instance that is threaded into every generator, so overrides apply atomically with no module-level mutation.

**Scalar overrides** (replace a single value):

| Key | Default | Surfaces in |
| --- | --- | --- |
| `tenant_id` | `a1b2c3d4-5e6f-4071-8293-94a5b6c7d8e9` | Every `TenantId`, `OrganizationId` in `RawEventData` |
| `tenant_domain` | `contoso.com` | Cloud / UPN domain, intra-org Message-Ids |
| `on_prem_ad_domain` | `contoso.local` | `AccountDomain` on Identity* tables |
| `on_prem_netbios_domain` | `CONTOSO` | NetBIOS form of the on-prem domain |
| `on_prem_sid_prefix` | `S-1-5-21-1004336348-1177238915-682003330` | `AccountSid` prefix (per-user RID is appended) |

**Collection overrides** (fully replace the default list — no merge):

| Key | Item shape (required fields **bold**) | Used by |
| --- | --- | --- |
| `domain_controllers` | **`name`**, **`ip`**, **`device_id`** | Identity* tables |
| `devices` | **`device_id`**, **`device_name`**, `os_platform`, `os_version`, `public_ip`, `local_ip`, `mac_address`, `machine_group`, `primary_user_upn` | Device* tables (DeviceEvents, DeviceProcessEvents, DeviceLogonEvents, …) |
| `processes` | **`file_name`**, **`folder_path`**, **`company`**, **`description`**, **`internal_file_name`**, **`original_file_name`**, **`product_name`**, **`product_version`**, **`command_lines`**, `integrity_level`, `elevation`, `signature_status`, `signer_type`, `parent` | `InitiatingProcess*` columns on every Device* table |
| `users` | **`display_name`**, **`upn`**, **`object_id`**, `type`, `device_name`, `device_id`, `last_password_change_days_ago`, `sam_account_name`, `sid_rid`, `given_name`, `surname`, `department`, `job_title`, `employee_id`, `city`, `country` | Almost every table |
| `ips` | **`ip`**, **`city`**, **`state`**, **`country`**, **`isp`**, **`category`**, **`latitude`**, **`longitude`** | Source IPs across cloud and email tables |
| `user_agents` | **`ua`**, **`platform`**, **`device_type`**, **`browser`** | `CloudAppEvents`, `EntraIdSignInEvents`, `IdentityLogonEvents` |
| `resources` | **`name`**, **`id`** | `EntraIdSignInEvents.ResourceDisplayName` / `.ResourceId` |
| `client_apps` | **`name`**, **`app_id`** | `EntraIdSignInEvents.Application` / `.ApplicationId` |
| `groups` | **`name`**, **`id`** | `GraphApiAuditEvents.RequestUri` (`/groups/{id}/…`) |
| `conditional_access_policies` | **`id`**, **`displayName`**, `enforcedGrantControls`, `enforcedSessionControls` | `EntraIdSignInEvents.ConditionalAccessPolicies` |
| `entra_sign_in_error_codes` | **`code`**, **`weight`**, `description` | `EntraIdSignInEvents.ErrorCode` distribution + `AuthenticationProcessingDetails` |
| `entra_spn_sign_in_error_codes` | **`code`**, **`weight`**, `description` | `EntraIdSpnSignInEvents.ErrorCode` distribution |

A fully documented example profile is shipped at the repo root as [`xdrgen.example.yaml`](./xdrgen.example.yaml) with sample values for every override — copy it and edit:

```bash
cp xdrgen.example.yaml xdrgen.yaml
uv run xdrgen generate xdrgen.yaml -n 100
```

#### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `-o`, `--output` | `telemetry.json` (file) / `telemetry/` (dir, with `--per-table`) | Output path. A file in default mode (overwritten each run); a directory in per-table mode (created if missing, existing files inside are not removed). |
| `-n`, `--count` | `10` | Number of events to generate. Ignored when `--indefinite` is set. |
| `--indefinite` | `false` | Run forever until interrupted with `Ctrl+C`. The flush cadence (`--flush-every`) keeps memory bounded across long runs. |
| `-i`, `--interval` | `1.0` | Seconds to wait between events. Set to `0` for no delay. |
| `--echo` | `false` | Also print every generated event to stdout as it is generated. |
| `--per-table` | `false` | Cross-cuts the active sink — file: per-event files; Kafka: one topic per table. |
| `--flush-every` | `10000` | Buffer this many events in memory before flushing them to disk. Lower values trade throughput for tighter memory; higher values batch more aggressively. The buffer is also flushed at end of run and on `Ctrl+C`. |
| `--sink` | `file` | Where events go: `file` writes JSON to disk; `kafka` produces to a broker (requires `--kafka-bootstrap`); `kustainer` ingests into a local Kusto emulator. |
| `--kafka-bootstrap` | _(unset)_ | Comma-separated Kafka bootstrap servers (e.g. `localhost:9092`). Required when `--sink kafka`. |
| `--kafka-topic` | `xdrgen` | Kafka topic events are produced to. Ignored when `--per-table` is set. |
| `--kafka-topic-prefix` | `xdrgen.` | Prefix prepended to per-table Kafka topic names. Used only with `--per-table` (e.g. `xdrgen.` → `xdrgen.CloudAppEvents`). Pass an empty string to use the bare table name. |
| `--kustainer-cluster` | `http://localhost:8080` | Kustainer (Kusto emulator) HTTP endpoint. Used only with `--sink kustainer`. |
| `--kustainer-database` | `NetDefaultDB` | Kustainer database events are ingested into. `NetDefaultDB` is the database that ships with the emulator. |
| `--kustainer-table-prefix` | _(empty)_ | Prefix prepended to every Kustainer table name. Empty by default — events go straight to the table named after their model (e.g. `CloudAppEvents`). |

Examples:

```bash
# 100 events, no delay between them, into a custom file
uv run xdrgen generate xdrgen.yaml -n 100 -i 0 -o ./out/cae.json

# 100 events, one JSON file per event, into ./out/events/
uv run xdrgen generate xdrgen.yaml -n 100 -i 0 -o ./out/events --per-table

# Stream events forever, one every 2 seconds (writes once interrupted)
uv run xdrgen generate xdrgen.yaml --indefinite -i 2
```

#### Sinks

Sinks live in [`sinks/`](./sinks/). Each module defines a sink (a `Sink`-protocol class — `write(batch)` and `close()`) plus a `build(...)` factory; `main._build_sink` returns one based on `--sink`. The `--per-table` and `--flush-every` flags are sink-agnostic — they're handled by `main` and apply uniformly to whichever sink is active.

Three sinks ship today:

- **`--sink file`** _(default)_ — JSON to disk. Single combined array, or per-event files with `--per-table`. See `sinks/file.py`.
- **`--sink kafka`** — produces JSON to a Kafka broker via `kafka-python`. The table name is used as the message key so partitioning stays consistent per table. See `sinks/kafka.py`.
- **`--sink kustainer`** — ingests directly into [Kustainer](https://learn.microsoft.com/en-us/azure/data-explorer/kusto-emulator-overview), Microsoft's official Kusto/ADX emulator, via the `azure-kusto-data` SDK. Each event lands in the table named after its Pydantic model (e.g. `CloudAppEvents`). The emulator does not implement streaming or queued ingestion, so the sink uses the universally-supported `.ingest inline` control command on the engine endpoint. See `sinks/kustainer.py`.

##### Adding a new sink

1. Drop a module in `sinks/` (e.g. `sinks/s3.py`) that exports a class implementing the `Sink` protocol from `sinks/base.py` plus a top-level `build(...)` factory returning an instance.
2. Add an entry to the `SinkChoice` enum in `main.py` and a branch in `_build_sink` that calls your factory with the relevant CLI flags.
3. Add CLI flags for any sink-specific config (mirror the `--kafka-*` pattern), and a unit test in `tests/test_sinks.py` that stubs out the underlying client so it doesn't need real infrastructure.

##### Testing the Kafka sink locally

A [`docker/docker-compose-kafka.yml`](./docker/docker-compose-kafka.yml) spins up a single-broker Kafka (KRaft mode, no Zookeeper) plus [Kafka UI](https://github.com/provectus/kafka-ui) so you can watch topics fill up:

```bash
docker compose -f docker/docker-compose-kafka.yml up -d
uv run xdrgen generate -n 100 -i 0 --sink kafka --kafka-bootstrap localhost:9092
# Then browse http://localhost:8080 → cluster `local` → Topics.
```

The compose file exposes two listeners on the broker — `localhost:9092` for clients on your host (xdrgen) and `kafka:29092` for clients on the compose network (Kafka UI). Mismatched listeners are the most common Kafka-in-Compose footgun; this split keeps both paths working.

##### Testing the Kustainer sink locally

A [`docker/docker-compose-kustainer.yml`](./docker/docker-compose-kustainer.yml) spins up the official `kustainer-linux` image (single HTTP endpoint on `8080`, unauthenticated, `NetDefaultDB` database). Tables aren't created automatically by the sink — bootstrap them once with [`scripts/create_kustainer_tables.py`](./scripts/create_kustainer_tables.py), which walks every Pydantic model under `./models/` and emits a `.create-merge table` for each. Re-running it after `xdrgen update-models` is safe — `.create-merge` only adds new columns, it never drops existing data.

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d
uv run python scripts/create_kustainer_tables.py
uv run xdrgen generate -n 100 -i 0 --sink kustainer
```

The script and the sink share their type mapping (`str`→`string`, `int`→`long`, `bool`→`bool`, `float`→`real`, `datetime`→`datetime`, anything else→`dynamic`) so the schema the script writes always matches the rows the sink emits. Pass `--dry-run` to print the control commands without touching the cluster, and `--cluster` / `--database` to point at a non-default emulator.

###### Querying the local emulator

Kustainer speaks the standard Kusto REST API at `http://localhost:8080/v1/rest/query` (queries) and `/v1/rest/mgmt` (control commands). Anything that talks to a real ADX cluster works against it — the only difference is the URL and the lack of authentication.

The lowest-friction option is the [Azure Data Explorer Web UI](https://dataexplorer.azure.com): sign in to your Microsoft account, click *+ Add* -> *Connection*, paste `http://localhost:8080` in the *Connection URI* text field and you get the same query editor you'd use against a real cluster. Browser-side it's a JS app; queries go directly from your browser to `localhost:8080`.

For a one-shot `curl`:

```bash
curl -s http://localhost:8080/v1/rest/query \
  -H 'Content-Type: application/json' \
  -d '{"db":"NetDefaultDB","csl":"CloudAppEvents | take 5"}'
```

Or from Python via the same SDK the sink uses:

```python
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

kcsb = KustoConnectionStringBuilder.with_no_authentication("http://localhost:8080")
client = KustoClient(kcsb)
response = client.execute("NetDefaultDB", "CloudAppEvents | summarize count() by ActionType")
for row in response.primary_results[0]:
    print(row["ActionType"], row["count_"])
```

`.show tables` (control command, run via `execute_mgmt`) is the quickest way to confirm the bootstrap script created everything before you start ingesting.

The image is x86_64 only; on Apple Silicon, set `--platform linux/amd64` in the compose file (Docker emulates, so it is slow). The emulator has no separate ingest URI, no streaming ingestion, no queued ingestion, and no authentication — `mcr.microsoft.com/azuredataexplorer/kustainer-linux` is for local development only.

#### Production-like data

The generators are hand-curated per table to produce realistic, *correlated* values rather than random noise — a single tenant ID, the same user pool, the same IP-to-geo mapping, and user agents paired with their matching OS / browser. Per-table specifics (what each generator does to mirror real Defender data) live in [`generators/PRODUCTION_LIKE_DATA.md`](./generators/PRODUCTION_LIKE_DATA.md).

#### Supported tables

The `generate` command currently has handcrafted generators for:

- `CloudAppEvents`
- `DeviceEvents`
- `DeviceFileCertificateInfo`
- `DeviceImageLoadEvents`
- `DeviceLogonEvents`
- `DeviceNetworkEvents`
- `DeviceNetworkInfo`
- `DeviceProcessEvents`
- `DeviceRegistryEvents`
- `EmailAttachmentInfo`
- `EmailEvents`
- `EmailPostDeliveryEvents`
- `EmailUrlInfo`
- `EntraIdSignInEvents`
- `EntraIdSpnSignInEvents`
- `GraphApiAuditEvents`
- `IdentityAccountInfo`
- `IdentityDirectoryEvents`
- `IdentityEvents`
- `IdentityLogonEvents`
- `IdentityQueryEvents`
- `UrlClickEvents`

Listing a table in the YAML that does not have a generator yet will fail fast with a list of available tables. More generators will be added over time.

### `update-models`

Fetches three CSVs from `Azure/Azure-Sentinel/Tools/Solutions Analyzer/`:

- `tables.csv` and `tables_reference.csv` — overlapping table catalogues. The union of rows whose `category` column contains `xdr` or `mde` (case-insensitive) defines the Defender XDR / MDE table set.
- `table_schemas.csv` — column-level schemas (table name, column name, type, description).

It then writes one Pydantic model per table into `./models/`.

```bash
uv run xdrgen update-models
```

System columns starting with `_` (e.g. `_BilledSize`, `_IsBillable`, `_ResourceId`) are skipped — only first-class table columns become model fields. All fields are `Optional[T] = Field(None, ...)` because XDR events are inherently sparse. Column descriptions from the source docs become Pydantic field descriptions.

```python
from models import CloudAppEvents

event = CloudAppEvents(
    ActionType="FileDownloaded",
    AccountDisplayName="Avery Chen",
    IPAddress="20.43.122.12",
)
```

You usually don't need to run this yourself — a [GitHub Actions workflow](./.github/workflows/update-models.yml) runs `update-models` daily at 06:00 UTC against `main`, and any diff in `./models/` is opened as a PR and squash-merged once lint and tests pass. So `main` always tracks the latest upstream Defender XDR / MDE schemas.

## Development

Everything below is for working on `xdrgen` itself, not for using the CLI.

### Formatting

The codebase is formatted with [`ruff`](https://github.com/astral-sh/ruff) (target Python 3.12, configured in `pyproject.toml`). Always run `ruff format` before committing changes:

```bash
# Format every file in-place
uv run ruff format .

# Or just check for drift without writing
uv run ruff format --check .
```

### Linting

The codebase is also linted with [`ruff`](https://github.com/astral-sh/ruff) (target Python 3.12, configured in `pyproject.toml`). Always run `ruff check --fix` before committing changes — safe fixes are applied automatically; anything left is for you to address:

```bash
# Lint every file and apply safe fixes in-place
uv run ruff check --fix .

# Or just report issues without writing
uv run ruff check .
```

### Running tests

The test suite lives under `tests/` and runs with `pytest`:

```bash
# Run everything
uv run pytest

# Run a single file
uv run pytest tests/test_telemetry.py

# Run a single test by name
uv run pytest tests/test_telemetry.py::test_identity_logon_events_terminate_at_a_known_dc

# Quieter output
uv run pytest -q
```
