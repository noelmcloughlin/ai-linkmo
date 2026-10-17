---
type: GlossaryTerm
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/glossary/risk
title: Risk
definition: A named, identified harm - for example `atlas-toxic-output` or `nist-confabulation`.
description: A named, identified harm carrying a persistent identifier, defined by one taxonomy and mappable to equivalents in others.
resource: docs/key-concepts.md
tags:
- glossary
- ontology
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
definedBy:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
- by: process:ktl-librarian
  at: "2026-10-16T23:49:47Z"
---

# Risk

A **risk** is a named, identified harm, such as `atlas-toxic-output` or `nist-confabulation`.

Each risk carries a persistent identifier and is defined by a [taxonomy](taxonomy.md). The `/risk` endpoint and `./ai risk` serve them. Because the identifier is stable and ontology-backed, the same risk can be referenced from a [control or action](control-action.md), matched against another framework's equivalent through a [crosswalk](crosswalk.md), and traced from a regulatory obligation down to a deployed mitigation.
