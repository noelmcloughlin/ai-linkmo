---
type: Playbook
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/playbooks/bring-your-own-data
title: Bring your own data (BYOD)
description: How to add institutional governance data - schema-compliant YAML dropped into byo/data/ is picked up by the CLI, API, web UI and graph export.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
timestamp: "2026-07-13"
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
---

# Bring your own data

1. Author a YAML file conforming to the ai-atlas-nexus AI Risk Ontology schema (see the [upstream util README](https://github.com/IBM/ai-atlas-nexus/blob/main/src/ai_atlas_nexus/ai_risk_ontology/util/README.md)).
2. Drop it into `byo/data/`. All access patterns pick it up via their `--byod` / curation modes.
3. Validate: `uv run linkml validate byo/data/*.yaml -s <site-packages>/ai_atlas_nexus/ai_risk_ontology/ai-risk-ontology.yaml`.

The nine shipped `byo/data/*.yaml` files (FINOS AIGF plus eight framework encodings) are worked examples of this pattern - each has a `datasets/` concept in this bundle. Retired examples live in `byo/olddata/`.
