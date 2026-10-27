---
type: GlossaryTerm
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/glossary/taxonomy
title: Taxonomy
definition: A framework's catalogue of risks and controls, for example NIST AI RMF or the FINOS AI Governance Framework.
description: A framework's catalogue of risks and controls, and the unit each BYOD data file and each `--isDefinedByTaxonomy` query is scoped to.
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
  at: "2026-10-14T02:10:40Z"
---

# Taxonomy

A **taxonomy** is a framework's catalogue of risks and controls. NIST AI RMF, the FINOS AIGF, ISO/IEC 42001 and the rest each contribute one.

It is the scoping unit throughout AI-LinkMO: the `/taxonomy` endpoint lists them, queries filter by `--isDefinedByTaxonomy` (for example `./ai risk --isDefinedByTaxonomy nist-ai-rmf`), and each `byo/data/*.yaml` file encodes one framework as a taxonomy plus its rows. Because every taxonomy is expressed in the same [AI Risk Ontology](../references/ai-risk-ontology.md), identifiers mean the same thing across frameworks, and that is what makes [crosswalks](crosswalk.md) mechanical rather than manual.
