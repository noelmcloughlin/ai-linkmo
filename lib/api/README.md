# AI-LinkMO Demo: API Architecture

FastAPI server with **dynamic endpoint generation** and **factory-pattern** handlers.

## Architecture Overview

The OpenAPI spec (`openapi.yaml`) is single source of truth (endpoints/parameters).

Business logic (in `handlers.py`) contains all handler functions for API operations.

Both try to align to [the Ontology](https://ibm.github.io/ai-atlas-nexus/ontology/).

Constants (`constants.py`, `lib/frontend/src/lib/constants.ts`) help maintainability.

The Dynamic endpoint generator (`server_dyanmic.py`), parses OpenAPI spec and
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
uv run python lib/api/validate_handlers.py

# Strict mode (fail on inconsistencies - for CI/CD)
uv run python lib/api/validate_handlers.py --strict

# Verbose mode (show all handlers and parameters)
uv run python lib/api/validate_handlers.py --verbose
```
