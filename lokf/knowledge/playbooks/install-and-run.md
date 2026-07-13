---
type: Playbook
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/playbooks/install-and-run
title: Install and run AI-LinkMO
description: How to build the environment and start each of the four access patterns - CLI, FastAPI backend, Svelte web UI, and Neo4j graph database.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
timestamp: "2026-07-13"
about:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/cli
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/web-ui
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/graph-db
---

# Install and run

Condensed from the root `README.md` (the authority - follow it for current detail).

1. **Build** (RHEL example): `scl enable gcc-toolset-12 bash`, then `MAX_JOBS=4 TORCH_CUDA_ARCH_LIST="8.6" uv sync`. Building the `ai-atlas-nexus` dependency with CUDA extensions takes ~12 min.
2. **FastAPI backend**: `uv run uvicorn lib.api.server:app --reload` (port 8000).
3. **Web UI**: `cd lib/frontend && npm install && npm run dev` (port 5173, proxies to :8000).
4. **CLI**: `./ai -h`; e.g. `./ai risk --taxonomy nist-ai-rmf`. Works offline (slowCLI) or against the API (fastCLI).
5. **Graph DB**: `./ai graph cypher --export --byod`, run Neo4j (podman/docker, ports 7474/7687), then `:source /examples/ai-risk-ontology.cypher` in cypher-shell.
6. **Tests**: `uv run python lib/test/check_tests.py`, then `./scripts/tests.sh fast` (~101 CLI cases in API and local modes).

If `ai-atlas-nexus` is upgraded, regenerate the UI schema with `gen-json-schema` into `lib/frontend/static/schema/ai-risk-ontology.json` (exact command in the README).
