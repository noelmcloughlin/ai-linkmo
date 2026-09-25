---
type: Playbook
genre: how-to
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/playbooks/install-and-run
title: Install and run AI-LinkMO
description: How to build the environment and start each of the four access patterns - CLI, FastAPI backend, Svelte web UI, and Neo4j graph database.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:36Z"
sources:
  - resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
    title: README, Install and Quick start
  - resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/install-notes.md
    title: Install notes
  - resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/neo4j.md
    title: Load the graph into Neo4j
  - resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/test/README.md
    title: Test suite README
about:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/cli
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/web-ui
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/graph-db
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:36Z"
---

# Install and run

Condensed from the root `README.md` and the pages it links (the authority: follow them for current detail).

1. **Build**: Python 3.11+ and `uv`, Node 22 for the web UI. `uv sync --extra test`, then `./ai --help`; that is the offline CLI, ready to use. An older gcc, a CUDA build or a corporate package index needs the extra steps in `docs/install-notes.md`.
2. **FastAPI backend**: `uv run uvicorn lib.api.server:app --reload` (port 8000). Its write endpoints are unauthenticated, so keep it on localhost.
3. **Web UI**: `cd lib/frontend && npm ci && npm run dev` (port 5173, proxies to :8000). The login is a persona picker, not authentication.
4. **CLI**: `./ai -h`; e.g. `./ai risk --isDefinedByTaxonomy nist-ai-rmf`. Works offline (slowCLI, `--mode local`) or against the API (fastCLI, the default).
5. **Graph DB**: `./ai graph cypher --export --byod`, run Neo4j in a container (podman or docker, ports 7474/7687) with `graph/cypher/` mounted at `/examples`, then `:source /examples/ai-risk-ontology.cypher` in `cypher-shell`. The steps are `docs/neo4j.md`.
6. **Tests**: `uv run pytest lib/test -m "not slow"` is what CI runs (about two minutes). `./scripts/tests.sh` has narrower modes; its default, `fast`, runs the CLI cases in API mode only, and `full` adds local mode (about 25 minutes).

If `ai-atlas-nexus` is upgraded, regenerate the UI schema with `gen-json-schema` into `lib/frontend/static/schema/ai-risk-ontology.json` (exact command in `docs/install-notes.md`).
