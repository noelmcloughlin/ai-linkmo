---
type: Service
genre: reference
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
timestamp: "2026-08-12T00:00:00Z"
references:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
dependsOn:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/finos-aigf
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:33:34Z"
generated:
  by: process:ktl-librarian
  at: "2026-10-14T02:10:40Z"
---

# Overview

The **FastAPI backend** (`lib/api/`) is the system-integration access pattern. `api.yaml` is the exposure file: it names the ontology classes the API lists, the path of each, and the hand-written operations (`/graph`, `/crosswalk`, `/inference`, `/schemaview`, `/byo`, `/ares`) as OpenAPI operation objects in its overlay. Everything else about a class comes from the LinkML schema in the installed `ai_atlas_nexus` package: each slot of the class is one query parameter, an enum slot offers its values, and a value outside them is a 422.

`exposure.py` joins the two into one view, which the API kernel and the [CLI](cli.md) both read. At startup `server_kernel.py` registers one GET per exposed class, routed to `handlers.query_class`, and binds each overlay operation to the `handlers` function its `operationId` names. `server.py` is the app itself: CORS, the cache-control middleware, the probes (`/health`, `/ready`, `/version`, `/classes`) and the cached `AIAtlasNexus` instances.

The contract is the server's `/openapi.json` (OpenAPI 3.1). `just gen-openapi` writes the same document to `docs/openapi.json` without a server, and `lib/test/test_contract_published.py` fails when that copy falls behind. Swagger UI at `/docs`, ReDoc at `/redoc` and Scalar at `/scalar` read it.

`AI_LINKMO_DATA_SOURCE` chooses where the class listings come from. `store` reads the [record store](../datasets/record-store.md), `library` keeps the `AIAtlasNexus` instance, and `auto`, the default, is the store when its files exist and the library otherwise. Related-risk lookups, crosswalks, inference and the SPARQL and SHACL surface stay on the library. The `byod` parameter adds the files under `byo/data/`, among them the FINOS AIGF encoding (hence `dependsOn`).

Run it locally with `uv run uvicorn lib.api.server:app --reload` (the endpoint above is the development default). The overlay declares an `ApiKeyAuth` scheme on `PUT /byo/{filename}`, but the demo server does not enforce it, so keep it on localhost. `lib/test/test_exposure.py`, `test_api_kernel.py`, `test_endpoints.py` and `test_data_source.py` check the exposure, the generated endpoints and the two data sources.
