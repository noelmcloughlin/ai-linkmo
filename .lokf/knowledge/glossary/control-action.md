---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/control-action
title: Control / Action
definition: Something you do or deploy to detect or mitigate a risk.
description: The mitigation side of the model - what an organisation does or deploys against a risk; served by the /control and /action endpoints.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/key-concepts.md
tags:
  - glossary
  - ontology
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:05Z"
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:05Z"
---

# Control / Action

A **control** (or **action**) is something you do or deploy to detect or mitigate a [risk](risk.md).

The key-concepts page introduces the two together as the mitigation side of the model; the ontology and API keep them as separate entities, served by the `/control` and `/action` endpoints (`./ai control`, `./ai action`). Controls link back to the risks they address - `./ai control --related --hasRelatedRisk atlas-toxic-output` answers "which controls mitigate toxic output?".
