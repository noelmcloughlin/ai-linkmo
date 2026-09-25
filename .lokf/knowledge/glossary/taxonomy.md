---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/taxonomy
title: Taxonomy
definition: A framework's catalogue of risks or controls - for example NIST AI RMF or the FINOS AI Governance Framework.
description: A framework's catalogue of risks/controls; the unit each BYOD data file and each `--isDefinedByTaxonomy` query is scoped to.
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

# Taxonomy

A **taxonomy** is a framework's catalogue of risks or controls - NIST AI RMF, the FINOS AIGF, ISO/IEC 42001 and the rest each contribute one.

It is the scoping unit throughout AI-LinkMO: the `/taxonomy` endpoint lists them, queries filter by `--isDefinedByTaxonomy` (e.g. `./ai risk --isDefinedByTaxonomy nist-ai-rmf`), and each `byo/data/*.yaml` file encodes one framework as a taxonomy plus its rows. Because every taxonomy is expressed in the same [AI Risk Ontology](../references/ai-risk-ontology.md), identifiers mean the same thing across frameworks - which is what makes [crosswalks](crosswalk.md) mechanical rather than manual.
