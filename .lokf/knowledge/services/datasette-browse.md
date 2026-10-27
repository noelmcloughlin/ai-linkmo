---
type: Service
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/datasette-browse
genre: reference
title: Datasette browse UI
description: Datasette over two SQLite databases built from the schema's gen-sqltables tables, packaged and bring-your-own data, served on port 8001 with schema-derived descriptions, facets, search and JSON and CSV exports.
endpoint: http://127.0.0.1:8001
resource: lib/browse
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/working-with-the-data.md
tags:
- datasette
- sqlite
- browse
derivedFrom:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
status: draft
verified:
- by: process:ktl-librarian
  at: "2026-10-16T23:49:47Z"
---

# Overview

[Datasette](https://datasette.io/) gives every class a table to filter, facet, search and export. `just build-browse` writes two SQLite databases under `lib/browse/data`: `atlas.sqlite` holds the packaged data and `byod.sqlite` adds the files under `byo/data/`. `just browse` serves them on port 8001 and builds them first if they are missing. Both recipes install the `browse` extra, Datasette and sqlite-utils, through uv. Nothing under `lib/browse/data` is committed.

The tables follow the schema. LinkML's `gen-sqltables` makes one table per class, abstract parents included, and a link table for each multivalued slot. Each record is written to its own class's table and to the table of every class above it, so a reference to an abstract parent resolves. `lib/browse/data/metadata.yaml` is written from the schema in the same build: it describes each table and column from its class and slot, and offers facets on enum and reference columns with few values.

The build lists the references that name a record the data does not hold. `lib/test/test_browse.py` checks the loader against a toy schema, and in its slow tests builds both databases of the real data and checks them against the library.
