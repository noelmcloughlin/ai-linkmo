---
type: Service
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/web-ui
title: Svelte Web UI
description: Vite + Svelte 5 single-page application for exploring AI governance data through the FastAPI backend, aimed at non-technical stakeholders.
endpoint: http://localhost:5173
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/frontend
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/frontend/README.md
tags:
  - frontend
  - svelte
  - spa
timestamp: "2026-07-13"
dependsOn:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
---

# Overview

The **Svelte Web UI** (`lib/frontend/`) is the human-exploration access pattern: a plain Vite SPA using Svelte 5 runes and `svelte-routing`, with a record viewer, curation (BYOD) mode, and persistent identifiers. The dev server (`npm run dev`, endpoint above) proxies the API endpoint paths (`/classes`, `/risk`, `/action`, `/health`, ...) to the FastAPI backend on port 8000.

Configuration lives in `src/lib/constants.ts` (endpoints, accordion groups, personas); the `API_ENDPOINTS` list in `vite.config.ts` must stay in sync with it and with the FastAPI routes. Quality gates: `npm run check`, `npm run lint`, `npm run test` (vitest), exercised by `.github/workflows/ui-tests.yml`.
