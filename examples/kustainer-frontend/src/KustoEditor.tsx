import { useEffect, useRef } from "react";

import { CLUSTER_URI, DATABASE, fetchShowSchema } from "./kustainer";
import { loadMonaco, type Monaco } from "./loadMonaco";

interface Props {
  initialValue: string;
  theme: "light" | "dark";
  onChange: (value: string) => void;
  onRun: (value: string) => void;
  onSchemaError: (message: string) => void;
}

const MONACO_THEME = { light: "vs", dark: "vs-dark" } as const;

export function KustoEditor({
  initialValue,
  theme,
  onChange,
  onRun,
  onSchemaError,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onRunRef = useRef(onRun);
  const onChangeRef = useRef(onChange);
  const onSchemaErrorRef = useRef(onSchemaError);
  onRunRef.current = onRun;
  onChangeRef.current = onChange;
  onSchemaErrorRef.current = onSchemaError;
  const initialThemeRef = useRef(theme);

  useEffect(() => {
    let cancelled = false;
    loadMonaco().then((monaco: Monaco) => {
      if (!cancelled) monaco.editor.setTheme(MONACO_THEME[theme]);
    });
    return () => {
      cancelled = true;
    };
  }, [theme]);

  useEffect(() => {
    if (!containerRef.current) return;

    let disposed = false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let editor: any = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let changeSub: any = null;

    (async () => {
      const monaco: Monaco = await loadMonaco();
      if (disposed || !containerRef.current) return;

      // monaco-kusto registers the language lazily. Wait until it shows up
      // before creating the editor so syntax highlighting + completion are
      // wired from the first paint instead of falling back to plain text.
      await new Promise<void>((resolve) => {
        const isReady = () =>
          monaco.languages
            .getLanguages()
            .some((l: { id: string }) => l.id === "kusto");
        if (isReady()) {
          resolve();
          return;
        }
        const handle = monaco.languages.onLanguage("kusto", () => {
          handle.dispose();
          resolve();
        });
      });
      if (disposed || !containerRef.current) return;

      editor = monaco.editor.create(containerRef.current, {
        value: initialValue,
        language: "kusto",
        theme: MONACO_THEME[initialThemeRef.current],
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        scrollBeyondLastLine: false,
        tabSize: 2,
      });

      changeSub = editor.onDidChangeModelContent(() => {
        onChangeRef.current(editor.getValue());
      });

      editor.addCommand(
        monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter,
        () => onRunRef.current(editor.getValue()),
      );

      try {
        const schema = await fetchShowSchema();
        if (disposed) return;
        const workerFactory = await monaco.languages.kusto.getKustoWorker();
        const model = editor.getModel();
        if (!model) return;
        const worker = await workerFactory(model.uri);
        await worker.setSchemaFromShowSchema(schema, CLUSTER_URI, DATABASE);
        // eslint-disable-next-line no-console
        console.log("[xdrgen] monaco-kusto schema applied");
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error("[xdrgen] schema setup failed", e);
        if (!disposed) {
          onSchemaErrorRef.current(e instanceof Error ? e.message : String(e));
        }
      }
    })();

    return () => {
      disposed = true;
      if (changeSub) changeSub.dispose();
      if (editor) editor.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={containerRef} style={{ height: "100%", width: "100%" }} />;
}
