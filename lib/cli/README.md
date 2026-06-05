# CLI Architecture - OpenAPI as Single Source of Truth

## Overview

This demo CLI provides command-line access to AI-LinkMO.

The OpenAPI specification (`lib/api/openapi.yaml`) is the **single source of truth** for all endpoints and parameters, used by CLI (`lib/cli`) and API (`lib/api`) for consistency and maintainability.

```ascii

lib/cli/
├── cli.py              # Main CLI tool (dynamically reads OpenAPI)
├── utils.py            # Helper utilities
└── README.md           # This file
```

CLI parameter metadata is extracted (`extract_parameters_from_spec()`) from the OpenAPI specification for consistency across both API and CLI.

The schema is converted to argparse format (`schema_to_argparse_config()`) perserving parameter names and descriptions, and the argparse configuration is dynamically created (`create_argument_parser()`).

Parameters added, removed, or modified in `lib/api/openapi.yaml` are automatically handled by the CLI.

## Usage

```bash
# CLI automatically reads from OpenAPI spec
./ai risk --taxonomy nist-ai-rmf

# View all available parameters (from OpenAPI)
./ai --help

# Verbose mode shows all parsed parameters
./ai risk --verbose

# Show only parameters relevant to 'risk' endpoint
./ai risk --help

# Show only parameters relevant to 'model' endpoint  
./ai model --help

# Show all parameters from all endpoints
./ai --help
```

**Validation:**
Validate all handlers match OpenAPI spec:

```bash
uv run python lib/test/validate_handlers.py
uv run python lib/test/validate_handlers.py --strict
uv run python lib/test/validate_handlers.py --verbose
```

## Status

### Common flags

| Flag                   | Purpose                                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| `--version`            | Print the CLI version and exit.                                                                      |
| `--mode {api,local}`   | API mode (fast, requires `uvicorn`) or local mode (slow, in-process).                                |
| `--timeout SECONDS`    | HTTP request timeout for API mode (default `30`).                                                    |
| `--byod`               | Use the alternate `AIAtlasNexus` instance backed by `byo/data/` overrides.                           |
| `--count`, `--pretty`, `--verbose` | Output controls (auto-detects TTY for `--pretty`).                                      |

### Server URL resolution

The CLI computes its default API base URL with `_resolve_default_api_base_url`:

- Unset `AI_ATLAS_API_URL` -> `http://localhost:8000`.
- `AI_ATLAS_API_URL` pointing at `localhost`, `127.0.0.1`, `::1`, or
  `0.0.0.0` is accepted unconditionally.
- A non-local host requires `AI_ATLAS_API_URL_ALLOW_REMOTE=1`; without
  the opt-in the CLI warns on stderr and falls back to localhost. This
  prevents an exfiltrated env var from silently redirecting every CLI
  query to a third-party host.
- Malformed values (missing scheme, non-http) also fall back.

`detect_server_url` trusts an explicitly-set `AI_ATLAS_API_URL` without
issuing a `/health` probe (avoids one extra round-trip per CLI call). When
no env override is present it probes `/health` on the default URL then on
configured fallback ports, caching results for 60 s. On `ConnectionError`
the cache is invalidated so the next call re-probes (or, for env-set URLs,
the next call simply re-tries the configured URL).

### Hardening notes

- The local-mode handler no longer leaks internal exception text -
  failures log the full traceback server-side and return a generic
  message.
- HTTP requests use `verify=True` explicitly and honour `--timeout`.
- Logging configuration runs from `main()` (not at module import time)
  and only quiets `ai_atlas_nexus` / `linkml` loggers, leaving the rest
  of the application's logging untouched.
- `EXCLUDED_PARAMS` is imported from `lib.api.constants` so the API and
  CLI agree on which CLI-only flags must never reach the backend.

### Tests

Run the fast suite (skips ~25 minute local-mode sweep):

```bash
uv run pytest lib/test/ -m "not slow"
```

New suites added in this iteration:

- `lib/test/test_api_url_resolution.py` - unit tests for the env-var allowlist.
- `lib/test/test_byo_put.py` - traversal / suffix / oversize / malformed-YAML on `PUT /byo`.
- `lib/test/test_endpoints.py` - `/version`, `/ready`, `/classes`, `/inference`, `Cache-Control`.
- `lib/test/test_validate_handlers.py` - pytest shim for the OpenAPI<->handler drift check.

