# AI-LinkMO Demo: API Architecture

A FastAPI server whose class listings are generated from the AI Risk Ontology schema.

## Architecture Overview

`api.yaml` is the exposure file. It names the ontology classes the API lists, the path of
each, and the hand-written operations (`/graph`, `/crosswalk`, `/inference`, `/schemaview`,
`/byo`, `/ares`) as OpenAPI operation objects in its overlay. Everything else about a class
comes from the LinkML schema shipped inside the installed `ai_atlas_nexus` package: each
slot of the class is one query parameter, an enum slot offers its values, and a value
outside them is a 422.

`exposure.py` joins the two into one view, `load_exposure()`, which the API kernel and the
CLI both read. Neither reads YAML or `SchemaView` itself.

`server_kernel.py` registers the endpoints at startup. `register_class_endpoints` adds one
GET per exposed class, with a signature built from the class's slots and a response model
built from the ontology's own Pydantic class, and routes it to `handlers.query_class`.
`register_hand_endpoints` adds the overlay's operations, each bound to the `handlers`
function its `operationId` names.

`handlers.py` holds `query_class`, which lists, filters or fetches the records of one class
and keeps the only per-class knowledge left, how the library looks records up by a related
risk, in `RELATED_LOOKUPS`; and the hand-written operations after it.

`server.py` is the app itself: CORS, the cache-control middleware, the probes and the
cached `AIAtlasNexus` instances.

The contract is `/openapi.json` (OpenAPI 3.1), which carries the ontology classes under
`components/schemas`. `just gen-openapi` writes the same document to `docs/openapi.json`
without a server, and `lib/test/test_contract_published.py` fails when that copy falls
behind, so the committed file is always the served one. Three references read it: Swagger UI
at `/docs`, ReDoc at `/redoc` and Scalar at `/scalar`.

## Adding or removing a class

Add or remove an entry under `expose.classes` in `api.yaml`, with its `path`, the
`collection` the library stores it under, and `related: true` when the library can look it
up by risk (then add its call to `RELATED_LOOKUPS`). `lib/test/test_exposure.py` checks that
every exposed class is in the schema and every filter is a slot of its class;
`lib/test/test_api_kernel.py` checks the contract and the envelope the web UI reads.

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
| `/ready`   | Readiness probe - 200 only when the default `AIAtlasNexus` is loaded.   |
| `/version` | Reports `api`, `ai_atlas_nexus`, and (when available) `git_sha`.        |
| `/classes` | Lists schema classes, optionally filtered by `taxonomy`/`vocabulary`.   |

The class listings (`/risk`, `/action`, ...) and the hand-written operations
are registered at startup by `server_kernel.py`, so a new slot in the ontology
is a new filter without a code change, and a new method on a hand path only
needs its operation object in the overlay of `api.yaml`.

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
  - The overlay in `api.yaml` declares an `ApiKeyAuth` security scheme on this
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
- **Lifespan**: server now fails fast if the default `AIAtlasNexus`
  instance can't initialise (the BYOD instance is still optional).
