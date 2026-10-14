---
type: Service
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/cli
title: AI-LinkMO CLI
description: Command-line tool (./ai) for querying AI governance data - risks, taxonomies, controls, models, evaluations, crosswalks - built dynamically from the OpenAPI specification.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/cli
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/cli/README.md
tags:
- cli
- automation
- ci-cd
generated:
  by: process:ktl-librarian
  at: "2026-10-14T02:10:40Z"
dependsOn:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
references:
- https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
- by: process:ktl-librarian
  at: "2026-09-25T20:31:56Z"
---

# Overview

The **AI-LinkMO CLI** (`./ai`, implemented in `lib/cli/cli.py`) is the automation and CI/CD access pattern. Its command tree is built from data. `lib/api/api.yaml` names the ontology classes the project exposes and the operations written by hand, and the LinkML schema inside the installed `ai_atlas_nexus` package gives each class its slots. `lib/api/exposure.py` joins the two, and `cli.py` turns the result into one click command per exposed class, with one option per slot, plus one command per hand path (`graph`, `crosswalk`, `inference`, `schemaview`, `byo`, `ares`). The [FastAPI backend](fastapi-backend.md) reads the same view, so the CLI and the API cannot drift apart.

Option names are the schema's slot names unchanged, so `--isDefinedByTaxonomy` means the same thing on every command and in the API. An enum slot offers its permissible values and rejects anything else with exit code 2. A slot added upstream becomes a filter without a code change, and adding or removing a class is one entry in `lib/api/api.yaml`.

The CLI has two modes. API mode (`--mode api`, the default) sends each query to the running FastAPI backend, hence `dependsOn`. Local mode (`--mode local`) runs in process and offline. `--byod` adds the files under `byo/data/` to the packaged data, and `./ai search` queries the [record store](../datasets/record-store.md)'s text index.

Tests: `lib/test/test_cli_kernel.py` checks that every exposed class is a command whose options are exactly its parameters, `lib/test/test_cli_api_identity.py` checks that the CLI and the API expose the same surface, and `lib/test/test_cli_examples.py` runs the commands listed in `docs/cli-examples.md`. CI runs `uv run pytest lib/test -m "not slow"`.
