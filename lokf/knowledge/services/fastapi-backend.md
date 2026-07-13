---
type: Service
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
title: FastAPI Backend
description: REST API serving AI governance data to the CLI, web UI, and external GRC tooling; endpoints are generated dynamically from the OpenAPI specification.
endpoint: http://localhost:8000
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/api
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/api/openapi.yaml
tags:
  - api
  - rest
  - integration
timestamp: "2026-07-13"
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
dependsOn:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/finos-aigf
---

# Overview

The **FastAPI backend** (`lib/api/`) is the system-integration access pattern and the single source of truth for the other services. `server_dynamic.py` parses `openapi.yaml` at startup and registers a FastAPI route per path (`/risk`, `/taxonomy`, `/control`, `/action`, `/model`, `/evaluation`, `/incident`, `/obligation`, `/principle`, ...), mapping each `operationId` to a factory-pattern handler in `handlers.py`.

Run locally with `uv run uvicorn lib.api.server:app --reload` (endpoint above is the dev default). Handlers query the ai-atlas-nexus ontology data plus any BYOD files dropped into `byo/data/` - the FINOS AIGF dataset ships in-repo (hence `dependsOn`), and the eight companion framework datasets load the same way.

Handler/spec consistency is enforced by `lib/test/validate_handlers.py` and the endpoint tests in `lib/test/test_endpoints.py`.
