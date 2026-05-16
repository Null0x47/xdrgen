import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteStaticCopy } from "vite-plugin-static-copy";

// We load Monaco + monaco-kusto via Monaco's AMD loader (the only setup
// monaco-kusto actually supports). Mirror their built `min` / `release/min`
// trees onto stable URLs under `/vendor/...` for both dev and build.
export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/monaco-editor/min/vs/**/*",
          dest: "vendor/monaco/vs",
        },
        // Place monaco-kusto under the `vs/language/kusto/` path Monaco's
        // AMD loader resolves to by default — AMD `paths` overrides set on
        // the main thread don't propagate into the language worker, so any
        // worker-side `importScripts`/`require` for bridge / language
        // service helpers would otherwise 404.
        {
          src: "node_modules/@kusto/monaco-kusto/release/min/**/*",
          dest: "vendor/monaco/vs/language/kusto",
        },
      ],
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api/kusto": {
        target: "http://localhost:8080",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/kusto/, ""),
      },
    },
  },
});
