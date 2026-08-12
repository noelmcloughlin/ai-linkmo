---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/risk
title: Risk
definition: A named, identified harm - for example `atlas-toxic-output` or `nist-confabulation`.
description: A named, identified harm carrying a persistent identifier, defined by one taxonomy and mappable to equivalents in others.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
tags:
  - glossary
  - ontology
timestamp: "2026-08-12T00:00:00Z"
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
---

# Risk

A **risk** is a named, identified harm - `atlas-toxic-output`, `nist-confabulation` and so on.

Each risk carries a persistent identifier and is defined by a [taxonomy](taxonomy.md); the `/risk` endpoint and `./ai risk` serve them. Because the identifier is stable and ontology-backed, the same risk can be referenced from a [control or action](control-action.md), matched against another framework's equivalent through a [crosswalk](crosswalk.md), and traced from a regulatory obligation down to a deployed mitigation.
