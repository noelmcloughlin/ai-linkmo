---
type: Explanation
genre: explanation
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/explanations/what-ai-linkmo-adds
title: What AI-LinkMO adds to AI Atlas Nexus
description: AI-LinkMO is a workshop built on IBM AI Atlas Nexus. It adds doors, encodings and checks but no ontology of its own, and its governance records carry no provenance yet.
resource: docs/for-the-curious.md
tags:
  - rationale
  - provenance
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
status: draft
references:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
relatedTo:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/org/ibm
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/explanations/why-linked-ai-governance
verified:
  - by: process:ktl-librarian
    at: "2026-10-27T01:10:23Z"
sources:
  - resource: docs/for-the-curious.md
    title: For the curious, Where this sits and What it does not add yet
  - resource: docs/architecture.md
    title: Architecture, Where this sits
  - resource: docs/cli-examples.md
    title: CLI examples, which says most of its commands are test cases
---

# What AI-LinkMO adds to AI Atlas Nexus

[Why linked AI governance](why-linked-ai-governance.md) says why the model is shared. This concept says whose model it is, and what this repository adds to it.

## Upstream provides the model

[IBM AI Atlas Nexus](../org/ibm.md) provides three things. The [AI Risk Ontology](../references/ai-risk-ontology.md) is the LinkML schema every CLI command, API route, UI form and graph label here is generated from. The packaged risk data carries the IBM AI Risk Atlas, its public taxonomies and the relationships between them. The related-risk, related-control and related-incident lookups, and so the [crosswalks](../glossary/crosswalk.md), follow those relationships through the `ai-atlas-nexus` library. The library loads the ontology and the data, and LinkML's generators produce the JSON Schema the web UI includes.

## This repository adds doors, encodings and checks

AI-LinkMO is a workshop built on those, with no ontology of its own. It adds:

- the four access patterns ([CLI](../services/cli.md), [API](../services/fastapi-backend.md), [web UI](../services/web-ui.md), [graph](../services/graph-db.md));
- nine governance frameworks encoded in the ontology's own classes as [bring-your-own-data](../glossary/byod.md) examples under `byo/data/`;
- crosswalks on screen and as files;
- a scripted walk through all four doors in `byo/notes/EXAMPLES.md`;
- most of the CLI examples, run as tests in API and local modes;
- curate mode, where a person adds, edits or deletes records in their own files through the web UI and `PUT /byo`.

## What it does not add yet: provenance

The governance records say what a risk or a control is, not who vouched for the encoding. Each `byo/data/` file names in a header comment the script and input that produced it, and every row carries the same `dateCreated`, the day the generator ran. Nothing records who checked an encoding against the framework's own text, from which edition, or when to look again, and the ontology has no field for it. Curate mode has the same gap: the persona a person picks is not an identity, and an edited record keeps no trace of who made the change. For an auditor that is the first question, and for all nine frameworks the answer today is that nobody has checked.
