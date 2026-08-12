---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/crosswalk
title: Crosswalk
definition: A machine-generated mapping of equivalent concepts between frameworks.
description: A generated mapping of equivalent concepts across two taxonomies, replacing hand-built spreadsheet crosswalks.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
tags:
  - glossary
  - ontology
timestamp: "2026-08-12T00:00:00Z"
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
relatedTo:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/nist-ai-rmf-crosswalks
---

# Crosswalk

A **crosswalk** is a machine-generated mapping of equivalent concepts *between* frameworks.

It is the direct answer to the manual-mapping problem: instead of analysts maintaining spreadsheets, `./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod` generates the mapping from the linked data, and the `/crosswalk` endpoint serves it. Mappings are graded by strength (exact, close, broad, narrow, related). The exported results ship as the [NIST AI RMF crosswalks](../datasets/nist-ai-rmf-crosswalks.md) CSVs.
