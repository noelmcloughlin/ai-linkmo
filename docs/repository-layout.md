# Repository layout

[The README](../README.md) says what AI-LinkMO is for. This is the tree behind it. Three toolchains live here: Python and uv at the root, Node in `lib/frontend/`, and a second uv project in `.lokf/`. [CONTRIBUTING.md](../CONTRIBUTING.md) has the dev setup and the pre-PR checklist.

```text
ai                      the CLI entry point (runs lib/cli through uv)
lib/cli/                argparse generated from the OpenAPI spec; fastCLI (via the API) or slowCLI (offline)
lib/api/                FastAPI backend; openapi.yaml is the source of truth for every route
lib/frontend/           Svelte 5 web UI (Vite; proxies to the API on :8000)
lib/test/               pytest suite; its API-mode CLI cases are the documented CLI examples, checked
graph/                  the exported ontology, crosswalk CSVs, and cypher/export.py for Neo4j
byo/data/               nine governance frameworks encoded for the AI Risk Ontology
byo/notes/EXAMPLES.md   a scripted walk through all four access patterns
byo/images/             screenshots of each door, and the architecture diagram
docs/
  key-concepts.md           the vocabulary the four doors share
  working-with-the-data.md  bring your own data, crosswalks, the graph export
  neo4j.md                  load the graph into Neo4j in a container
  cli-examples.md           every entity type, one command away
  install-notes.md          compilers, CUDA, corporate package indexes
  llm-inferencing.md        LLM inference and ARES, on infrastructure you run
  for-the-curious.md        what this adds over AI Atlas Nexus, what it leaves out, where it could go
  status.md                 status and caveats, the full list
  releasing.md              how this repository releases
  repository-layout.md      this page
.lokf/                  the sidecar: this repository's own knowledge bundle (knowledge/) and its tooling
knowledge_bundle        -> .lokf/knowledge, the bundle under a visible name, for folder pickers and Obsidian
.github/workflows/      tests, lint, the knowledge-bundle gates, releases
```

## Tests

The test suite runs 101 CLI cases in API mode and in local mode, and starts the API server for you. `uv run pytest lib/test -m "not slow"` is what CI runs, about two minutes; `./scripts/tests.sh` has the narrower modes. The web UI (`npm run check`, `npm run lint`, `npm test` in `lib/frontend/`) and the bundle (`cd .lokf && just lokf-validate`) have their own gates. [lib/test/README.md](../lib/test/README.md) has the detail.
