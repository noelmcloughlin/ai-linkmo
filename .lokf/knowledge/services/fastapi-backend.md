---
type: Service
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/fastapi-backend
title: FastAPI Backend
description: The REST API serving AI governance data to the CLI, the web UI and external GRC tooling. The linkmo project in `ai-risk-ontology-linkmo/` generates its endpoints from the exposure file and the LinkML schema, and its contract is the server's `/openapi.json`.
endpoint: http://localhost:8000
resource: lib/api
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/api/README.md
tags:
  - api
  - rest
  - integration
timestamp: "2026-08-12T00:00:00Z"
references:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
dependsOn:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/datasets/finos-aigf
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:33:34Z"
generated:
  by: process:ktl-librarian
  at: "2026-10-27T17:36:56Z"
sources:
  - resource: ai-risk-ontology-linkmo
    title: The linkmo project the linkmo copier template generated, with the exposure file, the kernels, the server, the browse build and its tests
  - resource: .copier-answers.linkmo.yml
    title: The answers the linkmo template was applied with
  - resource: lib/api/README.md
    title: The API's architecture, the data sources and the probes
---

# Overview

The **FastAPI backend** is the system-integration access pattern. The linkmo project in `ai-risk-ontology-linkmo/`, which the linkmo copier template generated, builds the app, and `lib/api/` holds what ai-linkmo adds. `lib/api/README.md` describes both.

The exposure file, `ai-risk-ontology-linkmo/exposure.yaml`, names the ontology classes the API lists and the path of each. It adds parameters beside the slots: `byod` on every class, and `hasRelatedRisk`, `related` and `related_ids` on the classes a risk relates to. Its overlay holds the hand-written operations (`/search`, `/graph`, `/crosswalk`, `/inference`, `/schemaview`, `/byo`, `/ares`) as OpenAPI operation objects. Everything else about a class comes from the LinkML schema in the installed `ai_atlas_nexus` package: each slot of the class is one query parameter, an enum slot offers its values, and a value outside them is a 422.

`ai_linkmo.exposure` joins the two into one view, which the API kernel and the [CLI](cli.md) both read. The kernel registers one GET per exposed class. It answers every listing from the project's data source, `src/ai_linkmo/atlas.py`, which passes the question to `query_records` in `lib/api/handlers.py`. Each hand-written operation's `operationId` names a function that `src/ai_linkmo/hand.py` imports from `lib/api/handlers.py`.

`lib/api/server.py` is the project's app with ai-linkmo's `/classes` added. The app sets the CORS policy and the cache headers, and serves the probes (`/health`, `/ready`, `/version`).

The contract is the server's `/openapi.json` (OpenAPI 3.1). `just gen-openapi` writes the same document to `docs/openapi.json` without a server, and `lib/test/test_contract_published.py` fails when that copy is out of date. It is read by Swagger UI at `/docs`, ReDoc at `/redoc` and Scalar at `/scalar`.

`AI_LINKMO_BACKEND` chooses where the class listings come from. `store` reads the [record store](../datasets/record-store.md), `library` answers from the `AIAtlasNexus` instance, and `auto`, the default, is the store when its files exist and the library otherwise. Related-risk lookups, crosswalks, inference and the SPARQL and SHACL surface use the library whichever source is chosen.

The `byod` parameter adds the files under `byo/data/`, among them the FINOS AIGF encoding, which this concept therefore `dependsOn`. Given with an id, `byod` still fetches that one record.

Run it locally with `uv run uvicorn lib.api.server:app --reload` (the endpoint above is the development default). The overlay declares an `ApiKeyAuth` scheme on `PUT /byo`, but the demo server does not enforce it, so keep it on localhost.

The linkmo project's tests check the exposure, the generated endpoints and the README's count cases, and `lib/test/test_endpoints.py` and `test_data_source.py` check the probes and the two data sources.
