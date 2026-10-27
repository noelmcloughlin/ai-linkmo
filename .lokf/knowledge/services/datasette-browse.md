---
type: Service
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/datasette-browse
genre: reference
title: Datasette browse UI
description: Datasette over SQLite databases built from the schema's gen-sqltables tables, one of the packaged data and one with the bring-your-own data added, served on port 8001 with schema-derived descriptions, facets, search and JSON and CSV exports.
endpoint: http://127.0.0.1:8001
resource: ai-risk-ontology-linkmo/src/ai_linkmo/browse.py
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/working-with-the-data.md
tags:
  - datasette
  - sqlite
  - browse
derivedFrom:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
generated:
  by: process:ktl-librarian
  at: "2026-10-27T17:36:28Z"
status: draft
verified:
  - by: process:ktl-librarian
    at: "2026-10-16T23:49:47Z"
---

# Overview

[Datasette](https://datasette.io/) gives every class a table to filter, facet, search and export. The linkmo project in `ai-risk-ontology-linkmo/` builds the databases, and its recipes install the `browse` extra, Datasette and sqlite-utils, through uv:

- `just build-browse` writes one SQLite database of the packaged data under `ai-risk-ontology-linkmo/browse`.
- `just build-browse-byod` writes another, with the files under `byo/data/` added, under `ai-risk-ontology-linkmo/browse-byod`.
- `just browse` serves the first on port 8001 and `just browse-byod` the second, and each builds its database first when it is missing.

Neither folder is committed. The [website](https://noelmcloughlin.github.io/ai-linkmo/) serves the packaged data's database in Datasette Lite.

The tables follow the schema. LinkML's `gen-sqltables` makes one table per class, abstract parents included, and a link table for each multivalued slot. Each record is written to its own class's table and to the table of every class above it, so a reference to an abstract parent resolves. The same build writes `metadata.yaml` beside each database from the schema: it describes each table and column from its class and slot, and offers facets on enum and reference columns with few values. The build also lists the references that name a record the data does not hold.

The linkmo project's `tests/test_browse.py` builds the database of the packaged data and checks that each class table holds its records, that search finds a record by its label, and that Datasette serves the folder.
