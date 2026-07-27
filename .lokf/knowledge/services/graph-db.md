---
type: Service
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/graph-db
title: Neo4j Graph Database
description: Graph-database access pattern - the exported knowledge graph is loaded into Neo4j via Cypher for relationship analysis and regulatory crosswalks.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/graph
tags:
  - graph
  - neo4j
  - cypher
timestamp: "2026-07-13"
dependsOn:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/knowledge-graph-export
---

# Overview

The **graph database** is the relationship-analysis access pattern. `./ai graph cypher --export --byod` generates Cypher (`graph/cypher/ai-risk-ontology.cypher`, produced by `graph/cypher/export.py` using cymple + linkml-runtime), which is imported into a Neo4j container via `cypher-shell` (`:source /examples/ai-risk-ontology.cypher`). The Neo4j Browser on port 7474 then supports schema visualization (`CALL db.schema.visualization()`) and cross-taxonomy relationship queries.

This service is ephemeral by design - it is rebuilt from the [knowledge-graph export dataset](../datasets/knowledge-graph-export.md) rather than being a system of record.
