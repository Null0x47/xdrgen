# Kustainer frontend

A small React + Vite app that lets you run KQL queries against a local Kustainer instance.

- KQL editor powered by [`@kusto/monaco-kusto`](https://github.com/Azure/monaco-kusto) (real Kusto highlighting + completion).
- Schemas are loaded from Kustainer at startup (`.show database schema as json`) and handed to the language worker, so completion matches the tables currently in the emulator.
- Run the query with the **Run** button or **Ctrl+Shift+Enter** inside the editor.
- Results render in [AG Grid](https://www.ag-grid.com/).

## Prereqs

1. Start Kustainer, create the tables, and register the Defender stub functions (from the repo root):

   ```bash
   docker compose -f docker/docker-compose-kustainer.yml up -d
   ```

   Watch the bootstrap progress with `docker logs -f xdrgen-kustainer-init`; the sidecar exits once tables and functions are in place. To re-run the bootstrap (e.g. after `update-models`) without restarting the emulator: `docker compose -f docker/docker-compose-kustainer.yml up kustainer-init`.
   
   [`scripts/create_kustainer_functions.py`](./scripts/create_kustainer_functions.py) registers stubs for Defender-XDR-exclusive Advanced Hunting functions (`FileProfile`, `AssignedIPAddresses`, `SeenBy`, `DeviceFromIP`) so pasted hunting queries parse and the in-browser editor's autocomplete picks them up. The stubs return empty / pass-through results — Kustainer can't reproduce the real engine plugins.

2. Generate some events so queries return rows:

   ```bash
   uv run xdrgen generate -n 500 -i 0 --sink kustainer
   ```

## Run

### Dockerised (default)

The `frontend` service in [`docker/docker-compose-kustainer.yml`](../../docker/docker-compose-kustainer.yml) builds and serves the bundle behind nginx alongside Kustainer:

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d
```

Open http://localhost:5173. nginx proxies `/api/kusto/*` → `http://kustainer:8080` on the compose network, so the browser never talks to Kustainer directly (avoids CORS).

Rebuild after editing `src/`:

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d --build frontend
```

### Local dev (npm)

For HMR while editing:

```bash
cd examples/kustainer-frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/kusto/*` → `http://localhost:8080`.
