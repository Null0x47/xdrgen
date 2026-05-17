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

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   profile      [PROFILE]  Optional YAML profile selecting tables and overriding tenant fixtures.                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --output                  -o      PATH                        Output path. Defaults to `./telemetry.json`, or       │
│                                                               `./telemetry/` with `--per-table`.                    │
│ --count                   -n      INTEGER RANGE [x>=1]        Number of events to generate (ignored with            │
│                                                               --indefinite).                                        │
│                                                               [default: 10]                                         │
│ --indefinite                                                  Run until interrupted with Ctrl+C.                    │
│ --interval                -i      FLOAT RANGE [x>=0.0]        Seconds to wait between events. [default: 1.0]        │
│ --echo                                                        Also print each event to stdout.                      │
│ --per-table                                                   Group events per-table: one file per event (file      │
│                                                               sink) or one topic per table (kafka).                 │
│ --flush-every                     INTEGER RANGE [x>=1]        Buffer this many events before flushing to the active │
│                                                               sink.                                                 │
│                                                               [default: 10000]                                      │
│ --sink                            [json|csv|kafka|kustainer]  Destination for events: `json`, `csv`, `kafka`, or    │
│                                                               `kustainer`.                                          │
│                                                               [default: json]                                       │
│ --kafka-bootstrap                 TEXT                        Kafka bootstrap servers, e.g. `localhost:9092`.       │
│                                                               Required for --sink kafka.                            │
│ --kafka-topic                     TEXT                        Kafka topic to produce to (ignored with --per-table). │
│                                                               [default: xdrgen]                                     │
│ --kafka-topic-prefix              TEXT                        Prefix for per-table Kafka topic names (only with     │
│                                                               --per-table).                                         │
│                                                               [default: xdrgen.]                                    │
│ --kustainer-cluster               TEXT                        Kustainer (Kusto emulator) HTTP endpoint.             │
│                                                               [default: http://localhost:8080]                      │
│ --kustainer-database              TEXT                        Kustainer database events are ingested into.          │
│                                                               [default: NetDefaultDB]                               │
│ --kustainer-table-prefix          TEXT                        Prefix prepended to every Kustainer table name.       │
│ --help                                                        Show this message and exit.                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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

# CSV output (default → ./telemetry.csv; --per-table → ./telemetry/{Table}-{n}.csv)
uv run xdrgen generate --sink csv
```

`--per-table` cross-cuts whichever sink is active — it changes how events are *grouped*, not where they go. For `json` and `csv` it becomes one file per event under `./telemetry/`; for `kafka` it becomes one topic per table (`{--kafka-topic-prefix}{TableName}`).

### Profile

The YAML profile is optional. Without one, every table that has a generator is emitted using the default `contoso.com` tenant fixture. With one, you can select a subset of tables and/or override fixtures so the stream looks like it came from *your* tenant. Every override below replaces the matching default in full — collections are never merged.

A fully documented example is shipped at [`profile.example.yaml`](./profile.example.yaml) — copy it and edit:

```bash
cp profile.example.yaml profile.yaml
uv run xdrgen generate profile.yaml -n 100
```

The profile is validated by Pydantic models in [`world.py`](./world.py); unknown keys, wrong shapes, and missing required sub-fields fail fast.

#### Overridable fixtures

**Tenant identity** (scalars)

- `tenant_id` — Entra tenant GUID stamped on every row.
- `tenant_domain` — primary verified domain (e.g. `contoso.com`).
- `on_prem_ad_domain` — on-prem AD FQDN used by Identity* / Device* logon rows.
- `on_prem_netbios_domain` — pre-Windows-2000 short domain name.
- `on_prem_sid_prefix` — shared SID prefix (`S-1-5-21-…`) for per-user RIDs.

**Shared identity pools**

- `users` — user / service-account / guest catalogue (drives every account-bearing row).
- `devices` — MDE-managed endpoints feeding every Device* table.
- `ips` — source IPs with paired geo / ISP / category fields.
- `user_agents` — UA / platform / device-type / browser tuples.
- `processes` — InitiatingProcess catalogue (paths, version-info, signed flags).
- `domain_controllers` — DCs that terminate Identity* logon / query / directory rows.
- `groups` — Entra ID directory groups surfaced in Graph URIs.

**Entra ID** (`EntraIdSignInEvents`, `EntraIdSpnSignInEvents`)

- `client_apps` — first-party / line-of-business client apps + real app IDs.
- `service_principals` — workload identities (app SPNs, managed identities, CI/CD).
- `resources` — `ResourceDisplayName` / `ResourceId` target catalogue.
- `conditional_access_policies` — CA policies serialized into the `ConditionalAccessPolicies` JSON column.
- `entra_sign_in_error_codes` — weighted user-sign-in `ErrorCode` distribution + descriptions.
- `entra_spn_sign_in_error_codes` — weighted workload-identity `ErrorCode` distribution.

**Graph API** (`GraphApiAuditEvents`)

- `graph_api_endpoints` — `{method, uri, workload, scope}` catalogue of Graph calls.
- `graph_api_locations` — Azure regions stamped on `Location`.
- `graph_api_status_codes` — weighted HTTP response-code distribution.

**Defender for Endpoint** (Device* tables)

- `device_event_actions` — weighted `{action, shape, weight}` pool for `DeviceEvents.ActionType` (`shape ∈ {file, network, registry, none}` drives the auxiliary column block).
- `device_network_action_types` — weighted `DeviceNetworkEvents.ActionType` pool.
- `device_registry_action_types` — weighted `DeviceRegistryEvents.ActionType` pool.
- `file_action_types` — weighted `DeviceFileEvents.ActionType` pool.
- `device_logon_types` — weighted `DeviceLogonEvents.LogonType` pool.
- `device_logon_protocols` — auth protocol pool (`Kerberos`, `Ntlm`, `NetLogon`).
- `device_logon_failure_reasons` — failure-reason strings used only on `LogonFailed`.
- `network_destinations` — `{port, url}` outbound destination pool for `DeviceNetworkEvents`.
- `network_adapters` — Wi-Fi / Ethernet / VPN adapters for `DeviceNetworkInfo`.
- `local_dns_servers` — local DNS resolver pool (sampled k=2 — uniform-only).
- `local_default_gateways` — default-gateway pool.
- `file_templates` — `{folder_template, file_name, kind}` for `DeviceFileEvents` (`kind ∈ {download, doc, temp, share}` drives row shape).
- `file_sensitivity_labels` — `{label, sublabel}` fallback for randomly classified local documents.
- `file_download_hosts` — hosts rendered into `FileOriginUrl` / `FileOriginReferrerUrl`.
- `code_signing_certificates` — cert catalogue for `DeviceFileCertificateInfo`.
- `signed_files` — filename pool driving `SHA1` on signed-binary rows.
- `crl_urls` — CRL distribution-point URLs.
- `loaded_libraries` — `{file_name, folder_path}` DLL / assembly pool for `DeviceImageLoadEvents`.
- `registry_targets` — `{key, value_name, value_data, value_type}` registry target pool.

**Cloud Apps** (`CloudAppEvents`)

- `cloud_apps` — `{name, app_id, instance_id, audit_source, actions}` connector catalogue.
- `cloud_app_file_names` — `ObjectName` pool for File-shaped activities.
- `cloud_app_mail_subjects` — `ObjectName` pool for Email-shaped activities.
- `cloud_app_group_names` — `ObjectName` pool for Group-shaped activities.

**Defender for Identity / unified IdentityEvents**

- `identity_auth_methods` — `AuthenticationMethod` pool (`IdentityAccountInfo`).
- `identity_risk_levels` — weighted `DefenderRiskLevel` distribution (0 = None .. 3 = High).
- `identity_directory_action_types` — weighted `IdentityDirectoryEvents.ActionType` pool.
- `identity_raw_actions` — `{action, application, target_kind, weight}` for `IdentityEvents` (`target_kind ∈ {user, group, app, policy}`).
- `identity_event_group_names` — group-name pool used as `TargetObjects.Name` for group actions.
- `identity_event_app_names` — app-name pool for app actions.
- `identity_logon_types` — weighted `IdentityLogonEvents.LogonType` pool.
- `identity_logon_protocols` — weighted `{protocol, port}` pool (Service/Batch still routes Kerberos).
- `identity_logon_failure_reasons` — failure-reason strings on `LogonFailed`.
- `identity_query_kinds` — weighted `{query_type, protocol, port}` pool for `IdentityQueryEvents`.
- `identity_query_group_targets` — `QueryTarget` strings for group queries.
- `identity_query_computer_targets` — `QueryTarget` strings for computer / `Resolve` queries.

**Email / URL clicks** (`Email*` + `UrlClickEvents`)

- `email_templates` — full pre-built email catalogue feeding every Email* + UrlClickEvents row (pivot key: `NetworkMessageId`).
- `email_post_delivery_paths` — `{action, action_type, trigger, result, delivery_location}` for `EmailPostDeliveryEvents`.
- `url_click_outcomes` — weighted `{action_type, is_clicked_through, threat_types, weight}` for `UrlClickEvents`.
- `url_click_workloads` — weighted source workload pool (`Email` / `Teams` / `Office`).

#### Weighted sampling (opt-in)

Every pool override accepts two YAML shapes:

1. **Bare list** — sample uniformly. Any per-entry `weight` is ignored.

   ```yaml
   devices:
     - device_id: ws01
       device_name: WS-01
     - device_id: ws02
       device_name: WS-02
   ```

2. **`{random: false, entries: [...]}`** — sample weighted. Every entry must declare `weight`; the profile loader fails fast otherwise.

   ```yaml
   devices:
     random: false
     entries:
       - device_id: ws01
         device_name: WS-01
         weight: 10
       - device_id: ws02
         device_name: WS-02
         weight: 1
   ```

Scalar pools (e.g. `cloud_app_file_names`, `local_dns_servers`, `graph_api_locations`) accept the same two shapes — either a bare string list, or `{random: false, entries: [{value, weight}, ...]}`.

Caveat: pools sampled with `random.sample` (k>1) — currently `local_dns_servers` and the DNS slot of `DeviceNetworkInfo` — still pick uniformly even when `random: false`. The validator still enforces weights are present.

#### Threat profiles

Ready-made profiles that shape the output stream like a specific attack technique live in [`examples/threat-profiles/`](./examples/threat-profiles/):

- [`azure-hound/`](./examples/threat-profiles/azure-hound/) — emits the 14 Microsoft Graph endpoints AzureHound walks during directory collection, sized to trip the [CloudBrothers GraphAPIAuditEvents detection](https://cloudbrothers.info/detect-threats-graphapiauditevents-part-3/).
- [`axios-npm/`](./examples/threat-profiles/axios-npm/) — replays the post-install dropper command lines from the trojanized `axios@1.14.1` / `axios@0.30.4` packages (via `plain-crypto-js@4.2.1`), shaped to fire the `DeviceProcessEvents` curl-execution query from Microsoft's [Axios npm supply-chain analysis](https://www.microsoft.com/en-us/security/blog/2026/04/01/mitigating-the-axios-npm-supply-chain-compromise/).

### Sinks

Sinks live in [`sinks/`](./sinks/). Four ship today:

- **`json`** _(default)_ — JSON to disk. See `sinks/json.py`.
- **`csv`** — CSV to disk. Default mode writes a single `./telemetry.csv` with a `_table,event_json` wrapper so heterogeneous events fit one file; `--per-table` writes one CSV per event under `./telemetry/` with the event's model columns as the header. See `sinks/csv.py`.
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

Handcrafted generators currently exist for: `CloudAppEvents`, `DeviceEvents`, `DeviceFileCertificateInfo`, `DeviceFileEvents`, `DeviceImageLoadEvents`, `DeviceLogonEvents`, `DeviceNetworkEvents`, `DeviceNetworkInfo`, `DeviceProcessEvents`, `DeviceRegistryEvents`, `EmailAttachmentInfo`, `EmailEvents`, `EmailPostDeliveryEvents`, `EmailUrlInfo`, `EntraIdSignInEvents`, `EntraIdSpnSignInEvents`, `GraphApiAuditEvents`, `IdentityAccountInfo`, `IdentityDirectoryEvents`, `IdentityEvents`, `IdentityLogonEvents`, `IdentityQueryEvents`, `UrlClickEvents`.

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
