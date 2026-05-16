// monaco-kusto talks to Monaco via Monaco's legacy `loadForeignModule` API,
// which only exists in Monaco's AMD build. So we load both from local copies
// served by vite-plugin-static-copy under /vendor/* via Monaco's AMD loader.
// `MONACO_BASE` is the directory *containing* `vs/`; the worker resolves
// `vs/...` paths against it, so pointing at `…/vs` would produce `…/vs/vs/…`.
// monaco-kusto is mirrored under `vs/language/kusto/` so the worker's default
// AMD resolution finds it without any path-override hackery.
const MONACO_BASE = "/vendor/monaco";
const MONACO_URL = `${MONACO_BASE}/vs`;

// Loose `any` is intentional — Monaco's runtime shape lives on the global
// `window.monaco` after AMD load, and pulling in the npm typings just to
// type this surface would conflict with the AMD-loaded copy at runtime.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Monaco = any;

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    require: any;
    monaco: Monaco;
    MonacoEnvironment?: { getWorkerUrl: (id: string, label: string) => string };
  }
}

let monacoPromise: Promise<Monaco> | null = null;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const tag = document.createElement("script");
    tag.src = src;
    tag.onload = () => resolve();
    tag.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(tag);
  });
}

export function loadMonaco(): Promise<Monaco> {
  if (monacoPromise) return monacoPromise;
  monacoPromise = (async () => {
    window.MonacoEnvironment = {
      getWorkerUrl: () =>
        `data:text/javascript;charset=utf-8,${encodeURIComponent(
          `self.MonacoEnvironment = { baseUrl: '${location.origin}${MONACO_BASE}/' };` +
            `importScripts('${location.origin}${MONACO_URL}/base/worker/workerMain.js');`,
        )}`,
    };

    await loadScript(`${MONACO_URL}/loader.js`);
    // Absolute URL so the worker (born from a `data:` URL, no origin of its
    // own) can fetch modules with `fetch()`.
    window.require.config({
      paths: { vs: `${location.origin}${MONACO_URL}` },
    });

    await new Promise<void>((resolve, reject) => {
      window.require(["vs/editor/editor.main"], resolve, reject);
    });
    await new Promise<void>((resolve, reject) => {
      window.require(
        ["vs/language/kusto/monaco.contribution"],
        resolve,
        reject,
      );
    });
    return window.monaco;
  })();
  return monacoPromise;
}
