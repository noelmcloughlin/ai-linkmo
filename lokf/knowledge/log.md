# Change Log

## 2026-07-13
* **Steady-state refresh**: re-verified all 31 concepts against their recorded
  `resource`/`derivedFrom` provenance (manifest identity, CLI/API OpenAPI
  wiring, frontend constants, graph CSV headers, all 9 `byo/data/*.yaml`
  headers and `url:` fields, org/reference facts) - no drift found. Swept the
  full README table of contents for orphans: confirmed `/ares` and LLM
  inferencing are real, code-backed endpoints (`handlers.py`, `cli.py`,
  `vite.config.ts`) but already covered generically by the dynamic
  OpenAPI-driven CLI/API service concepts, so no new concept was minted.
  Extended `playbooks/knowledge-sources.md` with the consciously-excluded
  README sections (§LLM Inferencing, §ARES Evaluation, §ADOPT?, §Curate your
  own Open Data, §Building Python Applications, §Research) so future refreshes
  don't need to re-investigate them.

## 2026-07-13
* **Bootstrap discovery** (lokf-librarian): swept the repository and replaced the
  scaffold's placeholder services with 31 real concepts - 4 services (CLI,
  FastAPI backend, Svelte web UI, Neo4j graph DB), 11 datasets (knowledge-graph
  export, NIST AI RMF crosswalks, and the nine `byo/data/*.yaml` framework
  encodings), 11 references (the external authorities those datasets encode),
  3 playbooks (knowledge-sources map, install-and-run, BYOD), and 2
  organizations (FINOS, IBM). Recorded the scrape map as
  `playbooks/knowledge-sources.md`; rebuilt all section indexes and the root TOC.

## 2026-07-13
* **Initialization**: Scaffolded the LOKF bundle for AI-LinkMO with placeholder
  services. Real concepts to follow.
* **Validation skipped**: `lokf validate` is not yet available in the toolkit
  (PyPI 0.2.0 and git main both lack the command). As a substitute,
  `lokf convert --format ttl knowledge` ran clean. Re-run validation once a
  toolkit release ships `validate` (the CI gate in
  `.github/workflows/knowledge-validate.yaml` will catch it).
