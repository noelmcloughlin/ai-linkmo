---
type: Dataset
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/nist-ai-rmf-crosswalks
title: NIST AI RMF crosswalks
description: CSV crosswalks mapping NIST AI RMF risks to the FINOS AIGF, the IBM Risk Atlas, and a demo institutional (acme) risk taxonomy.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/graph
tags:
  - crosswalk
  - mappings
timestamp: "2026-07-13"
distribution:
  - https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_finos-aigf.csv
  - https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_ibm-risk-atlas.csv
  - https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_acme-risk-taxonomy.csv
fields:
  - id
  - name
  - description
  - hasRelatedAction
  - isPartOf
  - close_mappings
  - exact_mappings
  - broad_mappings
  - narrow_mappings
  - related_mappings
  - expanded_risks
derivedFrom:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/nist-ai-rmf
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/finos-aigf
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
---

# Overview

Crosswalk documents map concepts between taxonomies, frameworks, standards and regulations. These CSVs are produced by the CLI, e.g. `./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod`: each row is a NIST AI RMF risk with its related GOVERN/MAP/MEASURE/MANAGE actions and its SKOS-style mappings (`exact`/`close`/`broad`/`narrow`/`related`) into the target taxonomy.

The acme crosswalk targets the demo institutional taxonomy retained in `byo/olddata/` (BYOD example, not active data).
