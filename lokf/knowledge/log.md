# Change Log

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
