# AI-LinkMO Demo: API Architecture

A FastAPI server whose class listings are generated from the AI Risk Ontology schema.

## Architecture Overview

The linkmo project in `ai-risk-ontology-linkmo/` builds the API. Its exposure file,
`ai-risk-ontology-linkmo/exposure.yaml`, names the ontology classes the API lists, the path
of each, the parameters ai-linkmo adds beside the slots (`byod`, and `hasRelatedRisk`,
`related` and `related_ids` on the classes a risk relates to), and the hand-written
operations (`/search`, `/graph`, `/crosswalk`, `/inference`, `/schemaview`, `/byo`, `/ares`)
as OpenAPI operation objects in its overlay. Everything else about a class comes from the
LinkML schema shipped inside the installed `ai_atlas_nexus` package: each slot of the class
is one query parameter, an enum slot offers its values, and a value outside them is a 422.

The project's kernels register one GET per exposed class and the overlay's operations, and
both the API and the CLI read the same exposure. Every listing goes to the project's data
source, `src/ai_linkmo/atlas.py`, which passes the question to `handlers.query_records`
here. Each hand operation's `operationId` names a function in `src/ai_linkmo/hand.py`, which
imports it from `handlers.py`.

`handlers.py` holds `query_records`, which lists, filters or fetches the records of one
class and keeps the only per-class knowledge left, how the library looks records up by a
related risk, in `RELATED_LOOKUPS`; and the hand-written operations after it.

`server.py` is the project's app, `ai_linkmo.server:app`, with ai-linkmo's `/classes` added.

The contract is `/openapi.json` (OpenAPI 3.1), which carries the ontology classes under
`components/schemas`. `just gen-openapi` writes the same document to `docs/openapi.json`
without a server, and `lib/test/test_contract_published.py` fails when that copy falls
behind, so the committed file is always the served one. Three references read it: Swagger UI
at `/docs`, ReDoc at `/redoc` and Scalar at `/scalar`.

## Adding or removing a class

Add or remove an entry under `expose.classes` in `ai-risk-ontology-linkmo/exposure.yaml`,
with its `path`, and the related parameters when the library can look it up by risk (then
add its call to `RELATED_LOOKUPS`). The linkmo project's tests check that every exposed
class is in the schema and every slot is a filter, and run the README's count cases in
`ai-risk-ontology-linkmo/tests/expected_counts.yaml` through the CLI and the API.

## Where the records come from

`AI_LINKMO_BACKEND` chooses the source of the class listings. `store` reads the DuckDB
files that `just load-store` builds through linkml-store, one collection per concrete class,
and answers a filter in milliseconds without loading the library. `library` keeps the
`AIAtlasNexus` instance, which re-parses the YAML on first use. `auto`, the default, is the
store when its files exist and the library otherwise. Related-risk lookups, crosswalks,
inference and the SPARQL and SHACL surface stay on the library whichever is chosen.
`lib/test/test_data_source.py` asks both sources the same questions and compares the answers.

A scope lists every instance of its class, wherever the data file placed it, so `/control`
holds every `RiskControl` including the Actions, and `/group` every `Group` subclass.

## FastAPI Server

The FastAPI server can be started in development mode:

```bash
uv run uvicorn lib.api.server:app --reload
```

## Status

Infrastructure endpoints surfaced by `server.py`:

| Endpoint   | Purpose                                                                 |
| ---------- | ----------------------------------------------------------------------- |
| `/health`  | Liveness probe - always 200 once the process is up.                     |
| `/ready`   | Readiness probe - 200 only when the data source has loaded.             |
| `/version` | Reports `api`, the schema's version, and the `datamodel` module.        |
| `/classes` | Lists schema classes, optionally filtered by `taxonomy`/`vocabulary`.   |

The class listings (`/risk`, `/action`, ...) and the hand-written operations
are registered by the linkmo project from its exposure file, so a new slot in
the ontology is a new filter without a code change, and a new method on a hand
path needs its operation object in the overlay and its function in `hand.py`.

### Security & operational hardening

- **CORS**: defaults to localhost dev origins. Override with
  `AI_LINKMO_CORS_ORIGINS="https://a.example,https://b.example"` (or `*`
  for permissive mode). Set `AI_LINKMO_CORS_ALLOW_NULL=1` to additionally
  allow `Origin: null` (file:// pages, sandboxed iframes).
- **PUT `/byo/{filename}`** is hardened against:
  - path traversal (filenames are constrained to `byo/data/` and must use
    `.yaml`/`.yml`),
  - oversize uploads (declared `Content-Length` and streaming check, cap is
    10 MiB),
  - malformed payloads (uploaded body is streamed to a temp file inside
    the target directory, `yaml.safe_load`-validated, then atomically
    promoted via `os.replace`; a `.bak` is taken first when an existing
    file is being overwritten).
  - The exposure file's overlay declares an `ApiKeyAuth` security scheme on this
    operation, and `/openapi.json` publishes it. The demo server does **not** enforce it - operators
    deploying outside localhost should add a reverse-proxy that validates
    `X-API-Key`.
- **`/inference`**: `gpu_memory_utilization` is a `float` (was a string).
- **`/ares`**: the `risks` array is capped at 200 entries (HTTP 413
  beyond that) to defend against memory-exhaustion payloads.
- **`/crosswalk`**: both `isDefinedByTaxonomy` and `isDefinedByTaxonomy2`
  are validated upfront; export filenames are sanitised so a crafted
  taxonomy ID can't escape `graph/`.
- **`/graph?id=cypher&export=true`**: uses `shutil.which("uv")`, runs
  with the project root as CWD, and applies a 300 s subprocess timeout.
- **Cache-Control middleware**: `GET` responses get `no-cache`, anything
  else `no-store`. Set the header explicitly on a response to opt out.
- **Lifespan**: the server loads the data source at startup, and the
  library with it unless the store answers the listings; `/ready` answers
  503 until it has. The BYOD instance loads on its first question.
