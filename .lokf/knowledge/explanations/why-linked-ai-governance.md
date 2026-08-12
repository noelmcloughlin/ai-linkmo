---
type: Explanation
genre: explanation
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/explanations/why-linked-ai-governance
title: Why linked AI governance
description: Why AI-LinkMO models governance as linked data behind four access patterns - the framework-fragmentation problem it answers, and why one shared ontology is what makes traceability auditable.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/README.md
tags:
  - rationale
  - ai-governance
timestamp: "2026-08-12T00:00:00Z"
about:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/cli
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/fastapi-backend
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/web-ui
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/services/graph-db
references:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
---

# Why linked AI governance

The other concepts in this bundle describe *what* AI-LinkMO is made of. This one records *why* it is shaped that way - the reasoning the root `README.md` opens with, which the mechanical descriptions do not carry.

## The problem: governance trapped in documents

AI governance mostly lives in PDFs and spreadsheets, and that creates three compounding difficulties:

- **Frameworks multiply.** NIST AI RMF, the EU AI Act, ISO/IEC 42001, the FINOS AIGF, the OWASP top-10s, SR 11-7 - each brings its own vocabulary for substantially overlapping risks and controls.
- **Mapping is manual.** Answering *"which of our controls satisfy both NIST and the EU AI Act?"* means analysts hand-building crosswalk spreadsheets: slow, error-prone, and stale the moment a framework updates.
- **Governance and engineering do not share a language.** Compliance teams work in policy clauses, engineers in pipelines and APIs, and nothing traces a regulatory obligation down to a deployed control.

## The wager: one model, four doors

AI-LinkMO's response is to model governance *once* as linked data - risks, controls, obligations, taxonomies, models, evaluations, incidents in a single LinkML ontology - and then expose that one model through four access patterns rather than four products: the [CLI](../services/cli.md) for engineers and pipelines, the [FastAPI backend](../services/fastapi-backend.md) for integrators and GRC tooling, the [web UI](../services/web-ui.md) for risk and compliance stakeholders, and the [graph database](../services/graph-db.md) for analysts.

The point of the four is *not* redundancy. Each constituency gets the same single source of truth in the form it can actually use, which is what stops governance and engineering from drifting into separate vocabularies again.

## Why the shared ontology is the load-bearing part

Because CLI, API, frontend and schema are all generated from the [same ontology](../references/ai-risk-ontology.md), a risk identifier means the same thing everywhere it appears. That identity is precisely what makes the traceability *auditable* rather than merely convenient: a [crosswalk](../glossary/crosswalk.md) becomes a mechanical derivation instead of an analyst's judgement call, and an [obligation](../glossary/obligation.md) can be followed to the [control](../glossary/control-action.md) that discharges it.

It is also why [BYOD](../glossary/byod.md) matters more than it first appears. Institutional policy encoded in the same schema is not a private annex bolted onto public data - it is queryable *alongside* it, on equal terms, which is the only way an organisation's own controls can participate in the same crosswalks as the frameworks it must answer to.
