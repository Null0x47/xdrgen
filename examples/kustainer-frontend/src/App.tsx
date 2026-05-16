import { useCallback, useEffect, useRef, useState } from "react";

import { KustoEditor } from "./KustoEditor";
import { PaneResizer } from "./PaneResizer";
import { ResultsGrid } from "./ResultsGrid";
import { ResultsToolbar } from "./ResultsToolbar";
import { RowDetailDrawer } from "./RowDetailDrawer";
import { clearAllTablesData, runQuery, type QueryResult } from "./kustainer";
import "./App.css";

const DEFAULT_QUERY = "CloudAppEvents\n| take 10";

const EDITOR_HEIGHT_KEY = "xdrgen-editor-height";
const EDITOR_MIN_PX = 80;
const EDITOR_DEFAULT_PX = 280;
// Leave headroom for header + grid; computed at clamp time against innerHeight.
const EDITOR_BOTTOM_RESERVE_PX = 160;

function clampEditorHeight(px: number): number {
  const max = Math.max(EDITOR_MIN_PX, window.innerHeight - EDITOR_BOTTOM_RESERVE_PX);
  return Math.min(max, Math.max(EDITOR_MIN_PX, px));
}

function initialEditorHeight(): number {
  const stored = Number(localStorage.getItem(EDITOR_HEIGHT_KEY));
  return clampEditorHeight(Number.isFinite(stored) && stored > 0 ? stored : EDITOR_DEFAULT_PX);
}

type Theme = "light" | "dark";

function initialTheme(): Theme {
  const stored = localStorage.getItem("xdrgen-theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function App() {
  const currentTextRef = useRef(DEFAULT_QUERY);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [selectedRow, setSelectedRow] = useState<Record<string, unknown> | null>(
    null,
  );
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [editorHeight, setEditorHeight] = useState<number>(initialEditorHeight);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("xdrgen-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem(EDITOR_HEIGHT_KEY, String(editorHeight));
  }, [editorHeight]);

  // Re-clamp when the viewport shrinks so the editor never pushes the grid offscreen.
  useEffect(() => {
    const onResize = () => setEditorHeight((h) => clampEditorHeight(h));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const handleResizerDrag = useCallback((deltaY: number) => {
    setEditorHeight((h) => clampEditorHeight(h + deltaY));
  }, []);

  const handleRun = useCallback(async (text: string) => {
    setRunning(true);
    setError(null);
    try {
      const r = await runQuery(text);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setResult(null);
    } finally {
      setRunning(false);
    }
  }, []);

  const handleChange = useCallback((text: string) => {
    currentTextRef.current = text;
  }, []);

  const handleSchemaError = useCallback((message: string) => {
    setError(
      `Schema load failed (autocomplete/highlighting will be limited): ${message}`,
    );
  }, []);

  const toggleTheme = useCallback(
    () => setTheme((t) => (t === "dark" ? "light" : "dark")),
    [],
  );

  const handleClear = useCallback(async () => {
    if (
      !window.confirm(
        "Remove all ingested data from Kustainer? Every row in every table will be dropped. Table definitions and functions stay.",
      )
    ) {
      return;
    }
    setClearing(true);
    setError(null);
    setNotice(null);
    try {
      const tables = await clearAllTablesData();
      setResult(null);
      setNotice(
        tables.length === 0
          ? "No tables to clear."
          : `Cleared ${tables.length} table${tables.length === 1 ? "" : "s"}.`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setClearing(false);
    }
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <strong>xdrgen</strong> — Kustainer
        </div>
        <div className="app-header-actions">
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            }
            title={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            }
          >
            {theme === "dark" ? "☀" : "☾"}
          </button>
          <button
            type="button"
            className="run-button"
            onClick={() => handleRun(currentTextRef.current)}
            disabled={running}
          >
            {running ? "Running…" : "Run ▶  (Ctrl+Shift+Enter)"}
          </button>
        </div>
      </header>
      <section
        className="editor-pane"
        style={{ flex: `0 0 ${editorHeight}px` }}
      >
        <KustoEditor
          initialValue={DEFAULT_QUERY}
          theme={theme}
          onChange={handleChange}
          onRun={handleRun}
          onSchemaError={handleSchemaError}
        />
      </section>
      <PaneResizer onDrag={handleResizerDrag} />
      {error && <div className="error-bar">{error}</div>}
      {!error && notice && (
        <div className="notice-bar" onClick={() => setNotice(null)}>
          {notice}
        </div>
      )}
      <section className="grid-pane">
        <ResultsToolbar
          result={result}
          clearing={clearing}
          onClear={handleClear}
        />
        <ResultsGrid
          result={result}
          theme={theme}
          onRowClick={setSelectedRow}
        />
      </section>
      <RowDetailDrawer row={selectedRow} onClose={() => setSelectedRow(null)} />
    </div>
  );
}
