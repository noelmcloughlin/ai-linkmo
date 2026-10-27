---
type: Service
genre: reference
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/cli
title: AI-LinkMO CLI
description: The command-line tool (`./ai`) for querying AI governance data such as risks, taxonomies, controls, models, evaluations and crosswalks. The linkmo project generates it, with one command per class its exposure file names and one option per slot of that class in the LinkML schema.
resource: ai-risk-ontology-linkmo/src/ai_linkmo/cli.py
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/cli-examples.md
tags:
  - cli
  - automation
  - ci-cd
generated:
  by: process:ktl-librarian
  at: "2026-10-27T17:36:28Z"
dependsOn:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/fastapi-backend
references:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:56Z"
---

# Overview

The **AI-LinkMO CLI** (`./ai`) is the automation and CI/CD access pattern. `./ai` runs `ai_linkmo`, the command line of the linkmo project in `ai-risk-ontology-linkmo/`, through `uv run`. The linkmo copier template generated that project, and ai-linkmo's uv workspace installs it.

The command tree is built from data. The exposure file, `ai-risk-ontology-linkmo/exposure.yaml`, names the ontology classes the project exposes and the operations written by hand. The LinkML schema inside the installed `ai_atlas_nexus` package gives each class its slots. `ai_linkmo.exposure` joins the two, and `ai_linkmo.cli` turns the result into one click command per exposed class, with one option per slot, plus one command per hand-written operation (`search`, `graph`, `crosswalk`, `inference`, `schemaview`, `byo`, `ares`). The [FastAPI backend](fastapi-backend.md) reads the same view, so the CLI and the API cannot drift apart.

Option names are the schema's slot names unchanged, so `--isDefinedByTaxonomy` means the same thing on every command and in the API. An enum slot offers its permissible values and rejects anything else with exit code 2. A slot added upstream becomes a filter without a code change, and adding or removing a class is one entry in the exposure file. A record's id goes after the command name, and `graph` and `inference` take their id the same way.

The CLI has two modes. API mode, the default, sends each query to the running FastAPI backend, so this concept `dependsOn` the backend. `./ai` makes it the default by setting `AI_LINKMO_MODE` to `api` when nothing else has set it. Local mode (`--mode local`) runs in process and offline, and calls the handler the API routes to.

API mode asks `http://localhost:8000`, or the URL in `AI_LINKMO_API_URL`. A URL on another host also needs `AI_LINKMO_API_URL_ALLOW_REMOTE=1`. Answers are JSON on stdout, indented on a terminal, and errors go to stderr. `--byod` adds the files under `byo/data/` to the packaged data, and `./ai search` queries the [record store](../datasets/record-store.md)'s text index.

In the tests, `lib/test/test_cli_kernel.py` checks that every exposed class is a command whose options are exactly its parameters, `lib/test/test_cli_api_identity.py` checks that the CLI and the API expose the same surface, and `lib/test/test_cli_examples.py` runs most of the commands listed in `docs/cli-examples.md`. CI runs `uv run pytest lib/test -m "not slow"` and the linkmo project's own tests.
