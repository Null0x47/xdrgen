// Thin client for the Kustainer REST API, proxied through Vite at `/api/kusto`.
export const DATABASE = "NetDefaultDB";
export const CLUSTER_URI = "http://localhost:8080";

const KUSTO_BASE = "/api/kusto";

export interface QueryColumn {
  name: string;
  type: string;
}

export interface QueryResult {
  columns: QueryColumn[];
  rows: unknown[][];
}

interface KustoTable {
  TableName: string;
  Columns: { ColumnName: string; DataType: string; ColumnType?: string }[];
  Rows: unknown[][];
}

interface KustoResponse {
  Tables: KustoTable[];
}

async function call(endpoint: "query" | "mgmt", csl: string): Promise<KustoResponse> {
  const res = await fetch(`${KUSTO_BASE}/v1/rest/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ db: DATABASE, csl }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Kustainer ${endpoint} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function runQuery(csl: string): Promise<QueryResult> {
  const data = await call("query", csl);
  const primary =
    data.Tables.find((t) => t.TableName === "Table_0") ?? data.Tables[0];
  if (!primary) {
    return { columns: [], rows: [] };
  }
  return {
    columns: primary.Columns.map((c) => ({
      name: c.ColumnName,
      type: c.ColumnType ?? c.DataType,
    })),
    rows: primary.Rows,
  };
}

// Empties every table in the database via `.clear table <T> data`. Table
// definitions and functions stay in place — only the ingested rows are
// dropped. Returns the list of tables that were cleared.
export async function clearAllTablesData(): Promise<string[]> {
  const data = await call("mgmt", ".show tables | project TableName");
  const rows = data.Tables[0]?.Rows ?? [];
  const tables = rows
    .map((r) => r[0])
    .filter((v): v is string => typeof v === "string");
  for (const name of tables) {
    await call("mgmt", `.clear table ['${name.replace(/'/g, "''")}'] data`);
  }
  return tables;
}

// `.show schema as json` returns a single result set whose single row's
// single cell is a JSON-encoded string holding the whole cluster schema in
// the shape monaco-kusto's `setSchemaFromShowSchema` expects.
export async function fetchShowSchema(): Promise<unknown> {
  const data = await call("mgmt", ".show schema as json");
  const cell = data.Tables[0]?.Rows[0]?.[0];
  if (typeof cell !== "string") {
    throw new Error("Unexpected schema response shape from Kustainer.");
  }
  const schema = JSON.parse(cell);
  if (import.meta.env.DEV) {
    const db = (
      schema as {
        Databases?: Record<
          string,
          {
            Tables?: Record<string, unknown>;
            Functions?: Record<string, unknown>;
          }
        >;
      }
    ).Databases?.[DATABASE];
    const tables = Object.keys(db?.Tables ?? {});
    const functions = Object.keys(db?.Functions ?? {});
    // eslint-disable-next-line no-console
    console.log(
      `[xdrgen] schema loaded: ${tables.length} table(s), ${functions.length} function(s) in ${DATABASE}`,
      { tables, functions },
    );
  }
  return schema;
}
