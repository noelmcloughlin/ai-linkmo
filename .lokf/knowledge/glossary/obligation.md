---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/obligation
title: Obligation
definition: A requirement a framework imposes, with evidence categories describing how you prove it.
description: A framework-imposed requirement together with the evidence categories that demonstrate compliance; served by the /obligation endpoint.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/key-concepts.md
tags:
  - glossary
  - ontology
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:05Z"
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
verified:
  - by: process:ktl-librarian
    at: "2026-09-25T20:31:05Z"
---

# Obligation

An **obligation** is a requirement a framework imposes, carrying evidence categories that describe how you prove you have met it.

The `/obligation` endpoint describes it as "a control activity (rule) describing an obligation for performing an activity". Obligations are what turn a regulatory text into something auditable: the requirement rows encoded from the [EU AI Act](../datasets/eu-ai-act.md) and similar frameworks are the regulatory end of the chain that runs obligation → [control/action](control-action.md) → [risk](risk.md).
