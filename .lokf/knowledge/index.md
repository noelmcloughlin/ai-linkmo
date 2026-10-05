---
lokf_version: "0.2"
okf_version: "0.2"
base_iri: https://github.com/noelmcloughlin/ai-linkmo/knowledge/
context: https://w3id.org/lokf/context.jsonld
title: AI-LinkMO Knowledge Bundle
description: A reference implementation of operational AI governance, demonstrating four DevSecOps-ready access patterns (CLI, FastAPI, Svelte web UI, and graph database) over open AI-governance data.
license: https://creativecommons.org/licenses/by/4.0/
publisher:
  type: Person
  id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/org/noel-mcloughlin
  name: Noel McLoughlin
---

# AI-LinkMO Knowledge Bundle

A [LOKF](https://lokf.nolan-nichols.com) knowledge base for AI-LinkMO. Every Markdown file under `knowledge/` is one concept; together they form a queryable knowledge graph, derived from this repository's code and docs.

## Services

The four access patterns ([index](services/index.md)):

* [AI-LinkMO CLI](services/cli.md) - Command-line tool (./ai) for querying AI governance data - risks, taxonomies, controls, models, evaluations, crosswalks - built dynamically from the OpenAPI specification.
* [FastAPI Backend](services/fastapi-backend.md) - REST API serving AI governance data to the CLI, web UI, and external GRC tooling; endpoints are generated dynamically from the OpenAPI specification.
* [Svelte Web UI](services/web-ui.md) - Vite + Svelte 5 single-page application for exploring AI governance data through the FastAPI backend, aimed at non-technical stakeholders.
* [Neo4j Graph Database](services/graph-db.md) - Graph-database access pattern - the exported knowledge graph is loaded into Neo4j via Cypher for relationship analysis and regulatory crosswalks.

## Datasets

Graph artifacts and BYOD framework encodings ([index](datasets/index.md)):

* [Knowledge-graph export (YAML + Cypher)](datasets/knowledge-graph-export.md) - Export of the AI risk knowledge graph - as ontology YAML (upstream ai-atlas-nexus data plus BYOD files) and as Cypher for Neo4j import (packaged data only).
* [NIST AI RMF crosswalks](datasets/nist-ai-rmf-crosswalks.md) - CSV crosswalks mapping NIST AI RMF risks to the FINOS AIGF, the IBM Risk Atlas, and a demo institutional (acme) risk taxonomy.
* [FINOS AIGF](datasets/finos-aigf.md), [EU AI Act](datasets/eu-ai-act.md), [FFIEC IT Handbook](datasets/ffiec-it-handbook.md), [ISO/IEC 42001](datasets/iso-42001.md), [NIST AI 600-1](datasets/nist-ai-600-1.md), [NIST SP 800-53 r5](datasets/nist-sp-800-53-r5.md), [OWASP LLM Top 10](datasets/owasp-llm-top-10.md), [OWASP ML Top 10](datasets/owasp-ml-top-10.md), [SR 11-7](datasets/sr-11-7.md)

## References

The external authorities the data encodes ([index](references/index.md)): [AI Risk Ontology](references/ai-risk-ontology.md), [FINOS AIGF](references/finos-aigf.md), [EU AI Act](references/eu-ai-act.md), [FFIEC IT Handbook](references/ffiec-it-handbook.md), [ISO/IEC 42001](references/iso-42001.md), [NIST AI RMF](references/nist-ai-rmf.md), [NIST AI 600-1](references/nist-ai-600-1.md), [NIST SP 800-53 r5](references/nist-sp-800-53-r5.md), [OWASP LLM Top 10](references/owasp-llm-top-10.md), [OWASP ML Top 10](references/owasp-ml-top-10.md), [SR 11-7](references/sr-11-7.md)

## Playbooks

([index](playbooks/index.md))

* [Knowledge sources map](playbooks/knowledge-sources.md) - The librarian's scrape map - every repository location and external URL this bundle derives concepts from, and how to re-verify each on a refresh run.
* [Install and run AI-LinkMO](playbooks/install-and-run.md) - How to build the environment and start each of the four access patterns - CLI, FastAPI backend, Svelte web UI, and Neo4j graph database.
* [Bring your own data (BYOD)](playbooks/bring-your-own-data.md) - How to add institutional governance data - schema-compliant YAML dropped into byo/data/ is picked up by the CLI, API and web UI with --byod, and by the YAML graph export, but not the Cypher export.

## Glossary

The domain vocabulary ([index](glossary/index.md)): [Taxonomy](glossary/taxonomy.md), [Risk](glossary/risk.md), [Control / Action](glossary/control-action.md), [Obligation](glossary/obligation.md), [Crosswalk](glossary/crosswalk.md), [Incident](glossary/incident.md), [Evaluation](glossary/evaluation.md), [Bring Your Own Data (BYOD)](glossary/byod.md)

## Explanations

([index](explanations/index.md))

* [Why linked AI governance](explanations/why-linked-ai-governance.md) - Why AI-LinkMO models governance as linked data behind four access patterns - the framework-fragmentation problem it answers, and why one shared ontology is what makes traceability auditable.
* [What AI-LinkMO adds to AI Atlas Nexus](explanations/what-ai-linkmo-adds.md) - AI-LinkMO is a workshop over IBM AI Atlas Nexus - it adds doors, encodings and checks but no ontology of its own, and its governance records carry no provenance yet.

## Organizations

([index](org/index.md)): [Noel McLoughlin](org/noel-mcloughlin.md), [FINOS](org/finos.md), [IBM](org/ibm.md)
