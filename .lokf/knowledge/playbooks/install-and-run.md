---
type: Playbook
genre: how-to
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/playbooks/install-and-run
title: Install and run AI-LinkMO
description: How to install AI-LinkMO and start its four doors (the CLI, the FastAPI backend, the Svelte web UI and the Neo4j graph database), then build the store, search it, browse it in Datasette and run the tests.
resource: docs/install.md
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
sources:
- resource: docs/install.md
  title: Install and Quick start
- resource: docs/install-notes.md
  title: Install notes
- resource: docs/neo4j.md
  title: Load the graph into Neo4j
- resource: docs/working-with-the-data.md
  title: Working with the data
- resource: lib/frontend/README.md
  title: Web UI README
- resource: lib/test/README.md
  title: Test suite README
- resource: scripts/tests.sh
  title: Test runner script
about:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/cli
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/fastapi-backend
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/web-ui
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/graph-db
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:31:36Z"
---

# Install and run

This playbook condenses `docs/install.md` and the pages it links, which are the authority for current detail.

1. **Build**: Python 3.11+ and `uv`, and Node 22 for the web UI. Run `uv sync --extra test`, then `./ai --help`: that is the offline CLI, ready to use. An older gcc, a CUDA build or a corporate package index needs the extra steps in `docs/install-notes.md`.
2. **FastAPI backend**: `uv run uvicorn lib.api.server:app --reload` listens on port 8000. Its write endpoints are not authenticated, so keep it on localhost.
3. **Web UI**: `cd lib/frontend && npm ci && npm run dev` serves port 5173 and proxies the API paths to port 8000. The login is a persona picker for the demo, not authentication.
4. **CLI**: `./ai -h`, then for example `./ai risk --isDefinedByTaxonomy nist-ai-rmf`. It sends queries to the API by default (`--mode api`) and works offline with `--mode local`.
5. **Graph database**: `just fetch-cypher` downloads the Cypher export. Run Neo4j in a container (podman or docker, ports 7474 and 7687) with `graph/cypher/` mounted at `/examples`, then run `:source /examples/ai-risk-ontology.cypher` in `cypher-shell`. `docs/neo4j.md` gives the steps.
6. **Store, search and browse**: `just load-store` builds the DuckDB store, `just index-store` builds its text index for `./ai search`, and `just browse` serves the data in Datasette on port 8001. `docs/working-with-the-data.md` gives the detail.
7. **Tests**: CI runs `uv run pytest lib/test -m "not slow"`. `./scripts/tests.sh` has narrower modes: its default, `fast`, runs the CLI cases in API mode only, and `full` adds local mode.

If `ai-atlas-nexus` is upgraded, regenerate the UI schema with `gen-json-schema` into `lib/frontend/static/schema/ai-risk-ontology.json`. `docs/install-notes.md` has the exact command.
