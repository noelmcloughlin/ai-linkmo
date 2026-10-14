---
type: Dataset
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/datasets/knowledge-graph-export
title: Knowledge-graph export (YAML + Cypher)
description: Export of the AI risk knowledge graph - as ontology YAML (upstream ai-atlas-nexus data plus BYOD files) and as Cypher for Neo4j import (packaged data only).
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/graph
tags:
- graph
- cypher
- export
generated:
  by: process:ktl-librarian
  at: "2026-10-14T02:10:40Z"
distribution:
- access_url: https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/ai-risk-ontology.yaml
  name: ai-risk-ontology.yaml
  media_type: application/yaml
- access_url: https://github.com/noelmcloughlin/ai-linkmo/blob/main/graph/cypher/ai-risk-ontology.cypher
  name: ai-risk-ontology.cypher
  media_type: application/x-cypher
derivedFrom:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:31:56Z"
---

# Overview

The knowledge graph has two distributions. `./ai graph --export --byod` writes the merged graph as `graph/ai-risk-ontology.yaml`: the packaged ai-atlas-nexus data plus the files under `byo/data/`. `just fetch-cypher`, or `./ai graph cypher --export`, downloads `graph/cypher/ai-risk-ontology.cypher`, the Cypher export ai-atlas-nexus publishes at the tag of the installed version. The saved file starts with three comment lines naming its source URL, its ai-atlas-nexus version and the fetch date, and it is not committed.

The two differ in scope. The YAML export honours `--byod`. The Cypher export is built upstream from the packaged data only, so `--byod` on it is refused with a 400. The Cypher distribution is what the [Neo4j graph database service](../services/graph-db.md) imports.

Both distributions are regenerable: the YAML from the packaged data and `byo/data/`, the Cypher from upstream's tagged release.
