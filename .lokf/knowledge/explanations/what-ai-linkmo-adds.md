---
type: Explanation
genre: explanation
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/explanations/what-ai-linkmo-adds
title: What AI-LinkMO adds to AI Atlas Nexus
description: AI-LinkMO is a workshop over IBM AI Atlas Nexus - it adds doors, encodings and checks but no ontology of its own, and its governance records carry no provenance yet.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/for-the-curious.md
tags:
  - rationale
  - provenance
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:32:51Z"
status: draft
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
relatedTo:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/org/ibm
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/explanations/why-linked-ai-governance
---

# What AI-LinkMO adds to AI Atlas Nexus

[Why linked AI governance](why-linked-ai-governance.md) says why the model is shared. This concept says whose model it is, and what this repository contributes on top.

## Upstream provides the model

[IBM AI Atlas Nexus](../org/ibm.md) provides three things. The [AI Risk Ontology](../references/ai-risk-ontology.md) is the LinkML schema every CLI command, API route, UI form and graph label here is generated from. The packaged risk data carries the IBM AI Risk Atlas, its public taxonomies and the relationships between them, which the related-record lookups and so the [crosswalks](../glossary/crosswalk.md) walk. The `ai-atlas-nexus` library loads both, and LinkML's generators produce the JSON Schema the web UI ships.

## This repository adds doors, encodings and checks

AI-LinkMO is a workshop that runs over those, with no ontology of its own. It adds the four access patterns ([CLI](../services/cli.md), [API](../services/fastapi-backend.md), [web UI](../services/web-ui.md), [graph](../services/graph-db.md)); nine governance frameworks encoded in the ontology's own classes as [bring-your-own-data](../glossary/byod.md) examples under `byo/data/`; crosswalks on screen and as files; a scripted walk through all four doors in `byo/notes/EXAMPLES.md`; most of the CLI examples run as tests in API and local modes; and curate mode, where a person edits records in their own files through `PUT /byo`.

## What it does not add yet: provenance

The governance records say what a risk or a control is, not who vouched for the encoding. Each `byo/data/` file names in a header comment the script and input that produced it, and every row carries the same `dateCreated`, the day the generator ran. Nothing records who checked an encoding against the framework's own text, from which edition, or when to look again, and the ontology has no field for it. Curate mode has the same gap: the persona a person picks is not an identity, and an edited record keeps no trace of who made the change. For an auditor that is the first question, and for all nine frameworks the answer today is that nobody has checked.
