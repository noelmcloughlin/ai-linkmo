---
type: Service
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/graph-db
title: Neo4j Graph Database
description: Graph-database access pattern - the exported knowledge graph is loaded into Neo4j via Cypher for relationship analysis and regulatory crosswalks.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/graph
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/neo4j.md
tags:
- graph
- neo4j
- cypher
generated:
  by: process:ktl-librarian
  at: "2026-10-14T02:10:40Z"
dependsOn:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/datasets/knowledge-graph-export
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:31:56Z"
---

# Overview

The **graph database** is the relationship-analysis access pattern. The project generates no Cypher of its own. `just fetch-cypher`, or `./ai graph cypher --export`, downloads the Cypher export that ai-atlas-nexus publishes at the release tag of the installed package to `graph/cypher/ai-risk-ontology.cypher`, which is not committed. That file is imported into a Neo4j container (podman or docker) with `cypher-shell` (`:source /examples/ai-risk-ontology.cypher`); `docs/neo4j.md` gives the steps. The Neo4j Browser on port 7474 then shows the schema (`CALL db.schema.visualization()`) and answers cross-taxonomy relationship queries.

The artefact is built upstream from the packaged ontology, so the graph shows the open frameworks and never the files under `byo/data/`. `--byod` on the Cypher export is refused with a 400 rather than ignored. `docs/neo4j.md` also lists defects in the upstream artefact, such as edge statements that match no node, which are upstream's to fix.

This service is ephemeral by design: it is rebuilt from the [knowledge-graph export dataset](../datasets/knowledge-graph-export.md) rather than being a system of record.
