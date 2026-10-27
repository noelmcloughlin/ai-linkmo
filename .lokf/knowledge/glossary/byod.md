---
type: GlossaryTerm
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/glossary/byod
title: Bring Your Own Data
abbreviation: BYOD
definition: Your internal policies encoded in the same schema, queryable alongside the open data.
description: The pattern of encoding institutional governance data in the AI Risk Ontology schema so it is served alongside the public frameworks.
resource: docs/key-concepts.md
tags:
  - glossary
  - byod
generated:
  by: process:ktl-librarian
  at: "2026-10-27T17:36:28Z"
relatedTo:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/playbooks/bring-your-own-data
verified:
  - by: process:ktl-librarian
    at: "2026-10-16T23:49:47Z"
---

# Bring Your Own Data (BYOD)

**BYOD** means your internal policies, encoded in the same schema as the public frameworks so that they are queryable alongside them.

In practice it is a schema-compliant YAML file in `byo/data/`. The CLI, the API and the web UI pick it up through the `--byod` flag or curate mode, and the exposure file, `ai-risk-ontology-linkmo/exposure.yaml`, declares the flag as the `byod` query parameter of every class. The Cypher export for the graph database refuses `--byod`, because ai-atlas-nexus builds that export from the packaged data alone. The nine framework encodings included in the repository are themselves worked BYOD examples. The [BYOD playbook](../playbooks/bring-your-own-data.md) gives the procedure.
