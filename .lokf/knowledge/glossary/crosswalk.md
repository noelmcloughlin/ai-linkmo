---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/crosswalk
title: Crosswalk
definition: A machine-generated mapping of equivalent concepts between frameworks.
description: A generated mapping of equivalent concepts across two taxonomies, replacing hand-built spreadsheet crosswalks.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/key-concepts.md
tags:
  - glossary
  - ontology
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:05Z"
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
relatedTo:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/nist-ai-rmf-crosswalks
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:05Z"
---

# Crosswalk

A **crosswalk** is a machine-generated mapping of equivalent concepts *between* frameworks.

It is the direct answer to the manual-mapping problem: instead of analysts maintaining spreadsheets, `./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod` generates the mapping from the linked data, and the `/crosswalk` endpoint serves it. Mappings are graded by strength (exact, close, broad, narrow, related). The exported results ship as the [NIST AI RMF crosswalks](../datasets/nist-ai-rmf-crosswalks.md) CSVs.
