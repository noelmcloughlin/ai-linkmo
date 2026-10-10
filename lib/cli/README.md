# CLI Architecture - one command per exposed class

## Overview

This demo CLI provides command-line access to AI-LinkMO.

The command tree is built from data. `lib/api/api.yaml` names the ontology classes the project exposes and the operations written by hand; the LinkML schema inside the installed `ai_atlas_nexus` package gives each class its slots. `lib/api/exposure.py` joins the two, and `cli.py` turns the result into one click command per exposed class, with one option per slot, plus one command per hand path (`graph`, `crosswalk`, `inference`, `schemaview`, `byo`, `ares`). The API kernel in `lib/api/server_kernel.py` reads the same view, so the CLI and the API cannot drift apart.

```ascii

lib/cli/
├── cli.py              # The click command tree, built from the exposure
├── utils.py            # Output, server detection and the cached library instance
└── README.md           # This file
```

Option names are the schema's slot names unchanged, so `--isDefinedByTaxonomy` means the same thing on every scope and in the API. An enum slot offers its permissible values and rejects anything else with exit code 2; an enum without values, such as `hasJurisdiction`, is a free string. A multivalued slot still takes one value, and a record matches when its list holds it.

A slot added upstream becomes a filter here without a code change. Adding or removing a class is one entry in `lib/api/api.yaml`.

## Usage

```bash
# One scope per exposed class
./ai risk --isDefinedByTaxonomy nist-ai-rmf

# The scopes
./ai --help

# The filters of one scope, one per slot of the class
./ai risk --help
./ai model --help

# One record by id, and the records related to it
./ai risk atlas-toxic-output
./ai risk atlas-toxic-output --related

# Verbose mode shows the parsed arguments and the library's log messages
./ai risk --verbose
```

**Checks:**
`lib/test/test_cli_kernel.py` checks that every exposed class is a command whose options are exactly its parameters, and `lib/test/test_exposure.py` checks that every parameter is a slot of its class.

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

- When `AI_ATLAS_API_URL` is unset, the default is `http://localhost:8000`.
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
- The shared options (`--mode`, `--timeout`, `--count`, `--verbose`,
  `--pretty`) are resolved by the CLI and never reach a handler or the server.

### Tests

Run the fast suite (skips ~25 minute local-mode sweep):

```bash
uv run pytest lib/test/ -m "not slow"
```

New suites added in this iteration:

- `lib/test/test_api_url_resolution.py` - unit tests for the env-var allowlist.
- `lib/test/test_byo_put.py` - traversal / suffix / oversize / malformed-YAML on `PUT /byo`.
- `lib/test/test_endpoints.py` - `/version`, `/ready`, `/classes`, `/inference`, `Cache-Control`.
- `lib/test/test_cli_kernel.py` - the command tree matches the exposure.
- `lib/test/test_api_kernel.py` - the generated endpoints and the published `/openapi.json`.
- `lib/test/test_exposure.py` - the exposure file, the schema and the library agree.
