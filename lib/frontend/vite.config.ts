import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { fileURLToPath, URL } from "node:url";
import { playwright } from "@vitest/browser-playwright";

import tailwindcss from "@tailwindcss/vite";

// Endpoint keys proxied to the backend API. Keep aligned with src/lib/entities.json (just gen-ui-config).
// Also includes infrastructure endpoints (classes, graph, crosswalk, inference, schemaview,
// byo, ares, organization, group, health) not surfaced as ENDPOINTS rows.
const API_ENDPOINTS = [
  "classes",
  "risk",
  "action",
  "control",
  "incident",
  "benchmarkcard",
  "evaluation",
  "document",
  "dataset",
  "adapter",
  "stakeholder",
  "intrinsic",
  "questionpolicy",
  "principle",
  "obligation",
  "recommendation",
  "requirement",
  "vocabulary",
  "model",
  "task",
  "taxonomy",
  "graph",
  "crosswalk",
  "inference",
  "schemaview",
  "byo",
  "ares",
  "organization",
  "group",
  "health",
  "version",
  "ready",
];

// Proxy /<endpoint> and /<endpoint>?... but not /<endpoint>/<id> (client-side routes).
const API_PROXY_REGEX = `^/(${API_ENDPOINTS.join("|")})(\\?.*)?$`;

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  // Static assets live in static/ (Vite's default is public/, which doesn't
  // exist here). Without this, `vite build` ships no schema/logo/robots.txt.
  publicDir: "static",
  resolve: {
    alias: {
      $lib: fileURLToPath(new URL("./src/lib", import.meta.url)),
      $components: fileURLToPath(
        new URL("./src/lib/components", import.meta.url),
      ),
      $states: fileURLToPath(new URL("./src/lib/states", import.meta.url)),
      $types: fileURLToPath(new URL("./src/lib/types", import.meta.url)),
      $utils: fileURLToPath(new URL("./src/lib/utils", import.meta.url)),
    },
  },
  server: {
    proxy: {
      [API_PROXY_REGEX]: {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    // Split vendor chunks to keep the main bundle lean.
    // Rolldown (Vite 8) requires manualChunks as a function.
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("svelte-routing") || id.includes("/svelte/"))
            return "vendor-svelte";
          if (id.includes("js-yaml")) return "vendor-yaml";
          if (id.includes("svelte-select")) return "vendor-select";
          return undefined;
        },
      },
    },
  },
  test: {
    // Run pure logic tests (state classes, utilities) in node, and component
    // tests that need a real DOM in the browser via Playwright.
    projects: [
      {
        extends: true,
        test: {
          name: "unit",
          environment: "node",
          include: ["src/**/*.{test,spec}.{js,ts}"],
          exclude: ["src/**/*.svelte.spec.{js,ts}", "node_modules", "dist"],
        },
      },
      {
        extends: true,
        // The record form's browser test imports app code whose dependencies
        // Vite would otherwise find only while the test runs. It then reloads
        // the page, and the test file fails to load whenever the cache is
        // cold, as it always is in CI.
        optimizeDeps: {
          include: [
            "@sjsf/ajv8-validator",
            "@sjsf/daisyui5-theme",
            "@sjsf/daisyui5-theme/extra-widgets/textarea-include",
            "@sjsf/form",
            "@sjsf/form/fields/extra/enum-include",
            "@sjsf/form/focus-on-first-error",
            "@sjsf/form/id-builders/modern",
            "@sjsf/form/mergers/modern",
            "@sjsf/form/resolvers/compat",
            "@sjsf/form/translations/en",
            "js-yaml",
            "tailwind-variants",
          ],
        },
        test: {
          name: "browser",
          include: [
            "src/**/*.svelte.spec.{js,ts}",
            "tests/**/*.svelte.spec.{js,ts}",
          ],
          browser: {
            enabled: true,
            provider: playwright(),
            headless: true,
            instances: [{ browser: "chromium" }],
          },
        },
      },
    ],
  },
});
