---
type: Dataset
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/datasets/nist-ai-rmf-crosswalks
title: NIST AI RMF crosswalks
description: CSV crosswalks mapping NIST AI RMF risks to the FINOS AIGF, the IBM Risk Atlas, and a demo institutional (acme) risk taxonomy.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/graph
tags:
- crosswalk
- mappings
timestamp: "2026-08-12T00:00:00Z"
distribution:
- access_url: https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_finos-aigf.csv
  name: crosswalk_nist-ai-rmf_to_finos-aigf.csv
  media_type: text/csv
- access_url: https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_ibm-risk-atlas.csv
  name: crosswalk_nist-ai-rmf_to_ibm-risk-atlas.csv
  media_type: text/csv
- access_url: https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/crosswalk_nist-ai-rmf_to_acme-risk-taxonomy.csv
  name: crosswalk_nist-ai-rmf_to_acme-risk-taxonomy.csv
  media_type: text/csv
fields:
- name: id
- name: name
- name: description
- name: hasRelatedAction
- name: isPartOf
- name: close_mappings
- name: exact_mappings
- name: broad_mappings
- name: narrow_mappings
- name: related_mappings
- name: expanded_risks
derivedFrom:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/nist-ai-rmf
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/finos-aigf
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
- by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:27:17Z"
sources:
- resource: graph
---

# Overview

Crosswalk documents map concepts between taxonomies, frameworks, standards and regulations. These CSVs are produced by the CLI, e.g. `./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod`: each row is a NIST AI RMF risk with its related GOVERN/MAP/MEASURE/MANAGE actions and its SKOS-style mappings (`exact`/`close`/`broad`/`narrow`/`related`) into the target taxonomy.

The acme crosswalk targets the demo institutional taxonomy retained in `byo/olddata/` (BYOD example, not active data).

The IBM Risk Atlas file, `crosswalk_nist-ai-rmf_to_ibm-risk-atlas.csv`, names its five mapping columns `closeMatch`, `exactMatch`, `broadMatch`, `narrowMatch` and `relatedMatch`. The FINOS and acme files name them `close_mappings`, `exact_mappings`, `broad_mappings`, `narrow_mappings` and `related_mappings`, as the `fields` list does.
