# Status and caveats

[The README](../README.md#status-and-caveats) gives the short version. This is the full list, kept in the present tense and revised as each item changes.

- **This is a demo.** The OpenAPI spec, the web UI and the CLI will all be reworked; treat their shapes as illustrative, not as a contract.
- **Keep it on localhost.** The write endpoints are unauthenticated, the web UI's login is a persona picker, and `graph/` is committed, regenerable output that the export commands rewrite in place. [SECURITY.md](../SECURITY.md) lists each limitation and what is planned.
- **`--byod` does not reach the Cypher export.** `graph/cypher/export.py` reads the packaged ontology only, so the [Neo4j walkthrough](neo4j.md) shows the open data, not your uploads.
- **Two encodings are thinner than their type suggests.** `byo/data/eu_ai_act.yaml` is a `RiskTaxonomy` of 308 requirement rows and no risks, so query it as `rule`, not `risk`; `ffiec_it_handbook.yaml` is a `RiskControlGroupTaxonomy` with groups and no controls.
- **No encoding has been checked by a named person against its framework's text.** Each header says which script produced it; the ontology has no field for a reviewer, and there has been none ([what it does not add yet](for-the-curious.md#what-it-does-not-add-yet-provenance)).
- **Nobody has confirmed a bundle concept yet.** All 39 are *Checked by automation only*; `ktl-curator` is how a person changes that. The bundle's `base_iri` is also a placeholder; moving it to a namespace the project controls rewrites every `id`, and has waited for a decision since 2026-08-05.
- **Slow paths.** `--mode local` loads the ontology in-process on every call, and the full local-mode test sweep takes about 25 minutes. LLM inferencing needs a vLLM host you run; ARES needs an upstream pull request ([llm-inferencing.md](llm-inferencing.md)).
