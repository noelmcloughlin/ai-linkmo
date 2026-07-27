---
type: Service
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/cli
title: AI-LinkMO CLI
description: Command-line tool (./ai) for querying AI governance data - risks, taxonomies, controls, models, evaluations, crosswalks - built dynamically from the OpenAPI specification.
resource: https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/cli
documentation: https://github.com/noelmcloughlin/ai-linkmo/blob/main/lib/cli/README.md
tags:
  - cli
  - automation
  - ci-cd
timestamp: "2026-07-13"
dependsOn:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
---

# Overview

The **AI-LinkMO CLI** (`./ai`, implemented in `lib/cli/cli.py`) is the automation and CI/CD access pattern. It reads `lib/api/openapi.yaml` - the single source of truth for endpoints and parameters - and generates its argparse interface dynamically, so parameter changes in the spec propagate to the CLI without code changes.

It has two modes: **fastCLI** delegates queries to the running FastAPI backend (hence `dependsOn`); **slowCLI** works offline against the bundled ai-atlas-nexus and BYOD data. Subcommands cover the ontology's entities (`risk`, `taxonomy`, `control`, `action`, `model`, `evaluation`, `incident`, ...) plus `crosswalk` and `graph --export` for Cypher/knowledge-graph output.

Tests: `lib/test/test_cli_examples.py` exercises every README example in both modes (`scripts/tests.sh`).
