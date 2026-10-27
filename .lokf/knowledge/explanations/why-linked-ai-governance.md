---
type: Explanation
genre: explanation
id: https://noelmcloughlin.github.io/ai-linkmo/knowledge/explanations/why-linked-ai-governance
title: Why linked AI governance
description: "Why AI-LinkMO keeps AI governance as one catalogue of linked data behind four doors (the CLI, the API, the web UI and the graph database): the problems of governance kept in PDFs and spreadsheets, and why one shared ontology makes the traceability auditable."
resource: docs/architecture.md
tags:
  - rationale
  - ai-governance
timestamp: "2026-08-12T00:00:00Z"
about:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/cli
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/fastapi-backend
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/web-ui
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/services/graph-db
references:
  - https://noelmcloughlin.github.io/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
  - by: process:ktl-librarian
    at: "2026-10-27T17:36:28Z"
generated:
  by: process:ktl-librarian
  at: "2026-10-17T00:24:57Z"
sources:
  - resource: docs/architecture.md
    title: Architecture, Why governance needs a catalogue and One model, four ways in
  - resource: docs/working-with-the-data.md
    title: Working with the data, Bring your own data
---

# Why linked AI governance

The other concepts in this bundle describe what AI-LinkMO is made of. This one records why it is shaped that way, as `docs/architecture.md` explains it.

## The problem: governance kept in documents

AI governance today mostly lives in PDFs and spreadsheets. That causes three problems:

- **Frameworks multiply.** NIST AI RMF, the EU AI Act, ISO/IEC 42001, FINOS AIGF, the OWASP LLM Top 10 and SR 11-7 each have their own vocabulary for overlapping risks and controls.
- **Mapping is manual.** To answer *"which of our controls satisfy both NIST and the EU AI Act?"*, an analyst builds a crosswalk spreadsheet by hand. It is slow to make, and it is stale the moment a framework updates.
- **Governance and engineering do not share a language.** Compliance teams work in policy clauses, and engineers work in pipelines and APIs. Nothing traces a regulatory obligation to a deployed control.

The knowledge already exists in the frameworks. What is missing is the catalogue: one model in which a risk, a control and the clause that requires it are each one record with one identifier. With that catalogue, the question above is a query rather than a quarter's work, and the answer is the same whoever asks it and however they ask.

## One model, four doors

AI-LinkMO closes that gap with one linked data model. The model is a LinkML ontology of risks, controls, obligations, taxonomies, models, evaluations and incidents. AI-LinkMO exposes it through four DevSecOps-ready access patterns, the four doors, so that every stakeholder gets the same model in the form they can use:

- the [CLI](../services/cli.md), for engineers and CI/CD pipelines;
- the [FastAPI backend](../services/fastapi-backend.md), for system integrators and GRC tools;
- the [Svelte web UI](../services/web-ui.md), for risk, compliance and business stakeholders;
- the [Neo4j graph database](../services/graph-db.md), for analysts and data scientists.

## Why the shared ontology matters

Every door is generated from the [same ontology](../references/ai-risk-ontology.md): the CLI, the API, the web UI and the schema. That is why a risk identifier means the same thing everywhere, and why the traceability is auditable.

The couplet at the top of the README describes the shape of the work. *Search out* the frameworks. Show *no favour* among them, with one ontology and one identifier for each thing. *Consult* them against each other, which is what a [crosswalk](../glossary/crosswalk.md) is. *Then act*, from a terminal, a pipeline, a browser or a graph query.

[Bring your own data](../glossary/byod.md) extends the same model to an organisation's own policies, taxonomies and controls. They live in the same model as the open frameworks, so one query spans public regulation and private practice.
