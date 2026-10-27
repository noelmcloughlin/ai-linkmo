---
type: Dataset
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/datasets/record-store
genre: reference
title: DuckDB record store
description: The packaged and bring-your-own records loaded through linkml-store into DuckDB, one collection per concrete class, which the API's class listings read once built, with a trigram search index and YAML dumps.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/store
tags:
- store
- duckdb
- search
derivedFrom:
- https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
sources:
- resource: docs/working-with-the-data.md
- resource: lib/store
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:27:17Z"
status: draft
verified:
- by: process:ktl-librarian
  at: "2026-10-16T23:49:47Z"
---

# Overview

`just load-store` loads the packaged data and the files under `byo/data/` through linkml-store into DuckDB files under `lib/store/data/`, one collection per concrete class. The files are not committed. The [FastAPI backend](../services/fastapi-backend.md) reads them when `AI_LINKMO_DATA_SOURCE` is `store`, or by default once they exist, and answers a filter without loading the library. `lib/test/test_data_source.py` asks the store and the library the same questions and compares the answers.

`just index-store` builds a trigram index over each record's id, name and description, kept in the same DuckDB files. `./ai search` and `GET /search` query it, and a scope whose index is missing answers 409. `just load-store` rebuilds the files without the index, so run `just index-store` again after it. `just dump-store` writes the store as YAML under `lib/store/data/dump`, one file per database.

`just validate-store` validates every collection against the schema and reports findings as JSON. CI loads the store and runs the validator with the 30 upstream data findings as the ceiling.
