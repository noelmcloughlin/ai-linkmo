# Change Log

## 2026-08-05
* **Schema migration (lokf toolkit upgrade)**: upgraded the lokf toolkit, which ships `lokf validate` (was
  previously unavailable). Running `lokf validate knowledge` against the upgraded schema (now backed by
  `linkml-validate`) revealed three breaking changes from the old `convert`-only validation:
  1. `timestamp` — changed from date-only (`YYYY-MM-DD`) to ISO 8601 datetime with timezone
     (`YYYY-MM-DDTHH:MM:SSZ`). Fixed across all 31 concepts.
  2. `distribution` — changed from a plain list of URL strings to a list of `Distribution` objects
     (`access_url`, `name`, `media_type`). Fixed in `datasets/knowledge-graph-export` and
     `datasets/nist-ai-rmf-crosswalks`.
  3. `fields` — changed from a plain list of strings to a list of `Field` objects (`name`). Fixed in
     `datasets/nist-ai-rmf-crosswalks`.
  Result: `OK — 31 concepts in knowledge validate against KnowledgeBundle.`

## 2026-07-27
* **Steady-state refresh**: re-verified all 31 concepts against their recorded
  provenance (source-map paths, CLI/API OpenAPI wiring, frontend Svelte 5 +
  proxy config, graph export tooling, all 9 `byo/data/*.yaml` headers and
  `url:` fields, index completeness) and projected the bundle to RDF
  (278 triples, 31 subjects, no dangling internal relation targets). One
  drift fixed: the sidecar was renamed `lokf/` -> `.lokf/` since the last run,
  so `playbooks/knowledge-sources.md` now names the `.lokf/` sidecar in its
  exclusion list (and makes `lib/frontend/STATUS.md` and the
  `knowledge-*.yaml` automation workflows conscious exclusions); the root
  README's LLM-visitors pointer to the bundle was repaired to `.lokf/`.

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
