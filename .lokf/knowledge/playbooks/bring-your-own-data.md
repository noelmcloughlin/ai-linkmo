---
type: Playbook
genre: how-to
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/playbooks/bring-your-own-data
title: Bring your own data (BYOD)
description: How to add institutional governance data - schema-compliant YAML dropped into byo/data/ is picked up by the CLI, API and web UI with --byod, and by the YAML graph export, but not the Cypher export.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/working-with-the-data.md
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:36Z"
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:36Z"
---

# Bring your own data

1. Author a YAML file conforming to the ai-atlas-nexus AI Risk Ontology schema (see the [upstream util README](https://github.com/IBM/ai-atlas-nexus/blob/main/src/ai_atlas_nexus/ai_risk_ontology/util/README.md)).
2. Drop it into `byo/data/`, or add and edit records there from the web UI's curate mode (saved through `PUT /byo`). The CLI, the API and the web UI pick it up with `--byod`.
3. Validate against the installed schema, `<site-packages>/ai_atlas_nexus/ai_risk_ontology/schema/ai-risk-ontology.yaml`; `docs/working-with-the-data.md` has the command that finds that path for you, then runs `uv run linkml validate byo/data/*.yaml -s "$SDIR/ai-risk-ontology.yaml"`.

The graph door is the exception. `./ai graph --export --byod` writes the merged YAML graph including your files, but `./ai graph cypher --export` runs `graph/cypher/export.py`, which reads the packaged ontology data only, so the Neo4j import shows the open frameworks and not your uploads.

The nine shipped `byo/data/*.yaml` files (FINOS AIGF plus eight framework encodings) are worked examples of this pattern - each has a `datasets/` concept in this bundle. Retired examples live in `byo/olddata/`.
