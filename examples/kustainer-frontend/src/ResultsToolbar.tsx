import { useCallback, useEffect, useRef, useState } from "react";

import type { QueryResult } from "./kustainer";

interface Props {
  result: QueryResult | null;
  clearing: boolean;
  onClear: () => void;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function exportJson(result: QueryResult) {
  const objects = result.rows.map((row) => {
    const obj: Record<string, unknown> = {};
    result.columns.forEach((c, i) => {
      obj[c.name] = row[i];
    });
    return obj;
  });
  downloadBlob(
    new Blob([JSON.stringify(objects, null, 2)], { type: "application/json" }),
    `xdrgen-results-${Date.now()}.json`,
  );
}

function escapeCsv(v: unknown): string {
  if (v === null || v === undefined) return "";
  const s = typeof v === "object" ? JSON.stringify(v) : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportCsv(result: QueryResult) {
  const lines: string[] = [];
  lines.push(result.columns.map((c) => escapeCsv(c.name)).join(","));
  for (const row of result.rows) {
    lines.push(row.map(escapeCsv).join(","));
  }
  downloadBlob(
    new Blob([lines.join("\n")], { type: "text/csv" }),
    `xdrgen-results-${Date.now()}.csv`,
  );
}

export function ResultsToolbar({ result, clearing, onClear }: Props) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const hasRows = !!result && result.rows.length > 0;

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleJson = useCallback(() => {
    setOpen(false);
    if (result) exportJson(result);
  }, [result]);

  const handleCsv = useCallback(() => {
    setOpen(false);
    if (result) exportCsv(result);
  }, [result]);

  return (
    <div className="results-toolbar">
      <span className="results-count">
        {result
          ? `${result.rows.length.toLocaleString()} row${result.rows.length === 1 ? "" : "s"}`
          : ""}
      </span>
      <div className="results-toolbar-actions">
        <button
          type="button"
          className="clear-button"
          onClick={onClear}
          disabled={clearing}
          title="Drop all rows in every table"
        >
          {clearing ? "Clearing…" : "Clear data"}
        </button>
        <div className="export-menu" ref={menuRef}>
          <button
            type="button"
            className="export-button"
            onClick={() => setOpen((o) => !o)}
            disabled={!hasRows}
            aria-haspopup="menu"
            aria-expanded={open}
          >
            Export ▾
          </button>
          {open && (
            <div className="export-menu-list" role="menu">
              <button
                type="button"
                role="menuitem"
                className="export-menu-item"
                onClick={handleJson}
              >
                JSON
              </button>
              <button
                type="button"
                role="menuitem"
                className="export-menu-item"
                onClick={handleCsv}
              >
                CSV
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
