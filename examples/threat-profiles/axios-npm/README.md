# Axios npm supply-chain compromise threat profile

Generates `DeviceProcessEvents` + `DeviceNetworkEvents` shaped like the
post-install dropper that ships with the trojanized `axios@1.14.1` /
`axios@0.30.4` packages (delivered through the planted
`plain-crypto-js@4.2.1` dependency) so the Defender hunting query in
Microsoft's writeup fires end-to-end against a local Kustainer / Sentinel.

Source:
[*Mitigating the Axios npm supply chain compromise*](https://www.microsoft.com/en-us/security/blog/2026/04/01/mitigating-the-axios-npm-supply-chain-compromise/),
Microsoft Security Blog, 2026-04-01.

## What it does

`profile.yaml` constrains the world to a single compromised developer
(`devon.marsh@northstar-labs.dev`) with three workstations — Windows, Linux
and macOS — and replaces the process catalogue with **only** the three
platform-specific dropper variants from the article. Every
`DeviceProcessEvents` row therefore carries one of these `ProcessCommandLine`
values, satisfying the `has_all(...)` terms in the published detection:

| Platform | `FileName` | Behaviour                                                                                                          |
|----------|------------|--------------------------------------------------------------------------------------------------------------------|
| Windows  | `cmd.exe`  | `curl` POSTs to `sfrclak.com:8000`, drops `%TEMP%\6202033.ps1`, launches it via `powershell -w hidden -ep bypass`, then `del`s it. |
| Linux    | `sh`       | `curl` POSTs to `sfrclak.com:8000`, drops `/tmp/ld.py`, `nohup python3 … > /dev/null 2>&1 &`.                       |
| macOS    | `bash`     | `curl` POSTs to `sfrclak.com:8000`, drops `/Library/Caches/com.apple.act.mond`, `chmod +x`, runs it backgrounded.   |

`world.ips` is pinned to the published C2 address `142.11.206.73` and
`world.network_destinations` is pinned to `(sfrclak.com, 8000)`, so every
`DeviceNetworkEvents` row carries `RemoteIP=142.11.206.73`,
`RemoteUrl=sfrclak.com`, and `RemotePort=8000` — satisfying both the
Defender `DeviceNetworkEvents` query and the Sentinel ASIM
`_Im_NetworkSession` / `_Im_WebSession` queries from the article.

`world.registry_targets` is pinned to the `MicrosoftUpdate` Run-key value
the Windows PowerShell RAT writes for persistence, so every
`DeviceRegistryEvents` row carries
`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run\MicrosoftUpdate`
with a `powershell.exe -w hidden -ep bypass …` payload.

Three follow-on RAT `Process` entries (Windows `powershell.exe`, Linux
`python3`, macOS `com.apple.act.mond`) have their `sha256` pinned to the
hashes published in the article, so `DeviceProcessEvents.SHA256` carries
them and analysts hunting by hash get hits. (For the macOS binary the hash
naturally belongs to the executable; for the Windows / Linux loaders the
article's hash is technically the dropped artefact's hash — we pin it on
the loader's DPE row because xdrgen doesn't ship a `DeviceFileEvents`
generator where it would land most naturally.)

## Run it

Send straight to the Kustainer emulator:

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d
uv run xdrgen generate examples/threat-profiles/axios-npm/profile.yaml \
    -n 600 -i 0 --sink kustainer
```

Or write to a JSON file and ingest it however you prefer:

```bash
uv run xdrgen generate examples/threat-profiles/axios-npm/profile.yaml \
    -n 600 -i 0 -o ./out/axios.json
```

`-n 600` gets ~200 rows per platform on average (uniform pick across the
3 dropper entries × 3 devices), which is plenty for each branch of the
DPE detection to land.

## Detection coverage

Compared against the four hunting queries in the Microsoft article:

| Query (table)                          | Fires? | Notes                                                                                                                              |
|----------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------|
| `DeviceProcessEvents` (curl execution) | ✅      | Primary signal. All three `has_all` branches are satisfied verbatim by the seeded `command_lines`.                                  |
| `DeviceNetworkEvents` (Defender, by URL+port) | ✅ | `RemoteUrl=sfrclak.com` + `RemotePort=8000` on every row via the `network_destinations` override.                                   |
| `DeviceRegistryEvents` (Run-key persistence)  | ✅ | Every row writes `…\Run\MicrosoftUpdate` via the `registry_targets` override — hunt with `RegistryKey endswith @"\Run"` + `RegistryValueName =~ "MicrosoftUpdate"`. |
| `_Im_NetworkSession` (ASIM, by IP)     | ✅      | `RemoteIP == 142.11.206.73` on every `DeviceNetworkEvents` row via the `ips` override.                                              |
| `_Im_WebSession` (ASIM, by IP)         | ✅      | Same `RemoteIP` pin; the query only filters on `DstIpAddr`.                                                                         |
| `DeviceTvmSoftwareInventory` (installed package) | ❌ | xdrgen doesn't generate the TVM software inventory table. |
| `CloudProcessEvents` (`node setup.js`) | ❌      | xdrgen doesn't generate `CloudProcessEvents`.                                                                                       |

## Detection query

Run this in Kustainer (or against the live Defender Advanced Hunting
schema). Source: Microsoft Security Blog, 2026-04-01.

```kql
DeviceProcessEvents
| where Timestamp > ago(2d)
| where (FileName =~ "cmd.exe" and ProcessCommandLine has_all ("curl -s -X POST -d", "packages.npm.org", "-w hidden -ep", ".ps1", "& del", ":8000"))
   or (ProcessCommandLine has_all ("curl", "-d packages.npm.org/", "nohup", ".py", ":8000/", "> /dev/null 2>&1") and ProcessCommandLine contains "python")
   or (ProcessCommandLine has_all ("curl", "-d packages.npm.org/", "com.apple.act.mond", "http://", ":8000/", "&> /dev/null"))
```

The original `Timestamp > ago(2d)` filter is kept because xdrgen writes
events whose `Timestamp` is "now"; it will match by default. Drop the
window when running against a long-running tenant if you want full history.

## IOCs replayed

| Type    | Value                                                  | Surfaces in                              |
|---------|--------------------------------------------------------|------------------------------------------|
| Domain  | `sfrclak.com`                                          | `DeviceProcessEvents.ProcessCommandLine` |
| URL     | `http://sfrclak.com:8000/` (+ `/6202033` on Windows)   | `DeviceProcessEvents.ProcessCommandLine` |
| IP      | `142.11.206.73`                                        | `DeviceNetworkEvents.RemoteIP`           |
| File    | `%TEMP%\6202033.ps1`                                   | `DeviceProcessEvents.ProcessCommandLine` |
| File    | `/tmp/ld.py`                                           | `DeviceProcessEvents.ProcessCommandLine` |
| File    | `/Library/Caches/com.apple.act.mond`                   | `DeviceProcessEvents.ProcessCommandLine` |
| Registry| `HKCU\…\Run\MicrosoftUpdate`                           | `DeviceRegistryEvents.RegistryKey` + `RegistryValueName` |
| SHA-256 | `ed8560c1ac7ceb6983ba995124d5917dc1a00288912387a6389296637d5f815c` (Windows PS RAT loader) | `DeviceProcessEvents.SHA256` |
| SHA-256 | `fcb81618bb15edfdedfb638b4c08a2af9cac9ecfa551af135a8402bf980375cf` (Linux Python loader) | `DeviceProcessEvents.SHA256` |
| SHA-256 | `92ff08773995ebc8d55ec4b8e1a225d0d1e51efa4ef88b8849d0071230c9645a` (macOS RAT binary) | `DeviceProcessEvents.SHA256` |
