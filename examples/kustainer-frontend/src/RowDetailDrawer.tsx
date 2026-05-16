import { useEffect, useMemo, useState } from "react";

type Row = Record<string, unknown>;

interface Props {
  row: Row | null;
  onClose: () => void;
}

// Grid cells stringify nested objects so they render as text. For the detail
// view we want the structured shape back, so try to re-parse JSON-looking
// string cells.
function expand(row: Row): Row {
  const out: Row = {};
  for (const [k, v] of Object.entries(row)) {
    if (typeof v === "string") {
      const trimmed = v.trim();
      if (
        (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
        (trimmed.startsWith("[") && trimmed.endsWith("]"))
      ) {
        try {
          out[k] = JSON.parse(v);
          continue;
        } catch {
          // fall through, keep the raw string
        }
      }
    }
    out[k] = v;
  }
  return out;
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "object") return JSON.stringify(v, null, 2);
  return String(v);
}

export function RowDetailDrawer({ row, onClose }: Props) {
  const [tab, setTab] = useState<"structured" | "json">("structured");

  // Close on Escape.
  useEffect(() => {
    if (!row) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [row, onClose]);

  const expanded = useMemo(() => (row ? expand(row) : null), [row]);

  if (!row || !expanded) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <header className="drawer-header">
          <strong>Event details</strong>
          <button
            type="button"
            className="drawer-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </header>
        <nav className="drawer-tabs">
          <button
            type="button"
            className={`drawer-tab ${tab === "structured" ? "active" : ""}`}
            onClick={() => setTab("structured")}
          >
            Structured
          </button>
          <button
            type="button"
            className={`drawer-tab ${tab === "json" ? "active" : ""}`}
            onClick={() => setTab("json")}
          >
            JSON
          </button>
        </nav>
        <div className="drawer-body">
          {tab === "structured" ? (
            <StructuredView row={expanded} />
          ) : (
            <pre className="json-view">{JSON.stringify(expanded, null, 2)}</pre>
          )}
        </div>
      </aside>
    </div>
  );
}

function StructuredView({ row }: { row: Row }) {
  const entries = Object.entries(row).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0) {
    return <div className="grid-empty">(all fields are empty)</div>;
  }
  return (
    <dl className="kv">
      {entries.map(([k, v]) => (
        <div key={k} className="kv-row">
          <dt>{k}</dt>
          <dd>{formatValue(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
