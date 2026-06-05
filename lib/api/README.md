# AI-LinkMO Demo: API Architecture

FastAPI server with **dynamic endpoint generation** and **factory-pattern** handlers.

## Architecture Overview

The OpenAPI spec (`openapi.yaml`) is single source of truth (endpoints/parameters).

Business logic (in `handlers.py`) contains all handler functions for API operations.

Both try to align to [the Ontology](https://ibm.github.io/ai-atlas-nexus/ontology/).

Constants (`constants.py`, `lib/frontend/src/lib/constants.ts`) help maintainability.

The Dynamic endpoint generator (`server_dynamic.py`), parses OpenAPI spec and
generates FastAPI endpoint functions on the fly, maps parameters to handler
functions, and validates request/responses.


```ascii
┌──────────────────────────────────────┐
│         openapi.yaml                 │  ← Single Source of Truth
│  - endpoints, paramters, handlers    │
└──────────────┬───────────────────────┘
               │ parsed by
┌──────────────▼───────────────────────┐
│       server_dynamic.py              │  ← Dynamic Generator
│  - register endpoints, map handlers  |
└──────────────┬───────────────────────┘
               │ registers with
┌──────────────▼───────────────────────┐
│         server.py                    │  ← Minimal Server
│  - FastAPI app initialization        │
│  - Dynamic endpoint registration     │
└──────────────┬───────────────────────┘
               │ calls
┌──────────────▼───────────────────────┐
│          handlers.py                 │  ← Business Logic
│  - handler functions/fetch factor    │
└──────────────┬───────────────────────┘
               │ uses
┌──────────────▼───────────────────────┐
│    lib/cli/utils.py                  │  ← Shared Utilities
└──────────────────────────────────────┘
```

## Factory Pattern Handlers

Handlers for basic entity queries (no related risk support) use default pattern:

```python
fetch_all=create_standard_fetch_all({
    'taxonomy': 'isDefinedByTaxonomy',    # param_name: query_field_name
    'document': 'hasDocumentation',
    'license': 'hasLicense'
})
```

Handlers with risk `related` and `related_ids` parameters use different parttern:

```python
fetch_all=create_related_fetch_all(
    related_method_name='get_related_actions',  # AIAtlasNexus method
    field_mappings={
        'taxonomy': 'isDefinedByTaxonomy',
        'document': 'hasDocumentation'
    },
    related_method_params=['taxonomy']  # Params to pass to related method
)
```

## FastAPI Server

The FastAPI server can be started in development mode:

```bash
uv run uvicorn lib.api.server:app --reload
```

## Handler Validation

Check handlers remain synchronized with the OpenAPI specification.
Consider adding to CI/CD pipeline:

```bash
# Validate handler signatures match OpenAPI
uv run python lib/test/validate_handlers.py

# Strict mode (fail on inconsistencies - for CI/CD)
uv run python lib/test/validate_handlers.py --strict

# Verbose mode (show all handlers and parameters)
uv run python lib/test/validate_handlers.py --verbose
```

A pytest shim (`lib/test/test_validate_handlers.py`) wraps the same check
so `uv run pytest` fails when handlers drift from `openapi.yaml`.

## Status

Infrastructure endpoints surfaced by `server.py`:

| Endpoint   | Purpose                                                                 |
| ---------- | ----------------------------------------------------------------------- |
| `/health`  | Liveness probe - always 200 once the process is up.                     |
| `/ready`   | Readiness probe - 200 only when the default `AIAtlasNexus` is loaded.   |
| `/version` | Reports `api`, `ai_atlas_nexus`, and (when available) `git_sha`.        |
| `/classes` | Lists schema classes, optionally filtered by `taxonomy`/`vocabulary`.   |

All dynamic endpoints (`/risk`, `/action`, ...) are generated from
`openapi.yaml` at startup by `register_endpoints_from_openapi` -
`server_dynamic.py` walks every HTTP method (`get`/`post`/`put`) declared
in the spec, so adding a new method to a path only requires updating the
YAML.

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
  - The OpenAPI spec declares an `ApiKeyAuth` security scheme on this
    operation. The demo server does **not** enforce it - operators
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

