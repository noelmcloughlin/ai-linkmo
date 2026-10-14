---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/byod
title: Bring Your Own Data
abbreviation: BYOD
definition: Your internal policies encoded in the same schema, queryable alongside the open data.
description: The pattern of encoding institutional governance data in the AI Risk Ontology schema so it is served alongside the public frameworks.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/key-concepts.md
tags:
- glossary
- byod
generated:
  by: process:ktl-librarian
  at: "2026-10-14T02:10:40Z"
relatedTo:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/playbooks/bring-your-own-data
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:31:05Z"
---

# Bring Your Own Data (BYOD)

**BYOD** is your internal policies encoded in the same schema as the public frameworks, so they are queryable alongside them.

Mechanically it is a schema-compliant YAML file dropped into `byo/data/`; every access pattern then picks it up through its `--byod` flag or curation mode (`lib/api/api.yaml` declares it as the `byod` query parameter). The nine framework encodings included in the repository are themselves worked BYOD examples. See the [BYOD playbook](../playbooks/bring-your-own-data.md) for the procedure.
