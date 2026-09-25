---
type: GlossaryTerm
genre: reference
id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/incident
title: Incident
definition: A realised risk, something that happened, linked back to the risks it demonstrates.
description: A documented occurrence of a risk, carrying its source and linked back to the risks it demonstrates; served by the /incident endpoint.
resource: https://github.com/noelmcloughlin/ai-linkmo/blob/main/docs/key-concepts.md
tags:
  - glossary
  - ontology
generated:
  by: process:ktl-librarian
  at: "2026-09-25T20:31:05Z"
status: draft
definedBy:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/references/ai-risk-ontology
relatedTo:
  - https://github.com/noelmcloughlin/ai-linkmo/knowledge/glossary/risk
---

# Incident

An **incident** is a realised [risk](risk.md): something that happened, linked back to the risks it demonstrates.

The `/incident` endpoint and `./ai incident` serve them. The packaged IBM AI Risk Atlas data supplies them, for example `ibm-risk-atlas-ri-fake-legal-cases`, a lawyer's brief citing cases that ChatGPT invented, with its source article recorded on the record. `byo/notes/EXAMPLES.md` starts from `chatgpt-samsung-leak`, company data leaked through ChatGPT, and follows `./ai incident chatgpt-samsung-leak --related` to its risks and on to the [controls](control-action.md) that cover them.
