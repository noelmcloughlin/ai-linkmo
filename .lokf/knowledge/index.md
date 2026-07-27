---
lokf_version: "0.1"
okf_version: "0.1"
base_iri: https://github.com/noelmcloughlin/ai-linkmo/knowledge/
context: https://w3id.org/lokf/context.jsonld
title: AI-LinkMO Knowledge Bundle
description: A reference implementation of operational AI governance, demonstrating four DevSecOps-ready access patterns (CLI, FastAPI, Svelte web UI, and graph database) over open AI-governance data.
license: https://creativecommons.org/licenses/by/4.0/
publisher:
  type: Organization
  id: https://github.com/noelmcloughlin/ai-linkmo/knowledge/org/noel-mcloughlin
  name: Noel McLoughlin
---

# AI-LinkMO Knowledge Bundle

A [LOKF](https://lokf.nolan-nichols.com) knowledge base for AI-LinkMO. Every Markdown file under `knowledge/` is one concept; together they form a queryable knowledge graph, derived from this repository's code and docs.

## Services

The four access patterns ([index](services/index.md)):

* [AI-LinkMO CLI](services/cli.md) - command-line access for automation and CI/CD.
* [FastAPI Backend](services/fastapi-backend.md) - REST API generated from the OpenAPI spec.
* [Svelte Web UI](services/web-ui.md) - Vite + Svelte 5 SPA for exploration.
* [Neo4j Graph Database](services/graph-db.md) - relationship analysis over the exported graph.

## Datasets

Graph artifacts and BYOD framework encodings ([index](datasets/index.md)):

* [Knowledge-graph export (YAML + Cypher)](datasets/knowledge-graph-export.md)
* [NIST AI RMF crosswalks](datasets/nist-ai-rmf-crosswalks.md)
* [FINOS AIGF](datasets/finos-aigf.md), [EU AI Act](datasets/eu-ai-act.md), [FFIEC IT Handbook](datasets/ffiec-it-handbook.md), [ISO/IEC 42001](datasets/iso-42001.md), [NIST AI 600-1](datasets/nist-ai-600-1.md), [NIST SP 800-53 r5](datasets/nist-sp-800-53-r5.md), [OWASP LLM Top 10](datasets/owasp-llm-top-10.md), [OWASP ML Top 10](datasets/owasp-ml-top-10.md), [SR 11-7](datasets/sr-11-7.md)

## References

The external authorities the data encodes ([index](references/index.md)): [AI Risk Ontology](references/ai-risk-ontology.md), [FINOS AIGF](references/finos-aigf.md), [EU AI Act](references/eu-ai-act.md), [FFIEC IT Handbook](references/ffiec-it-handbook.md), [ISO/IEC 42001](references/iso-42001.md), [NIST AI RMF](references/nist-ai-rmf.md), [NIST AI 600-1](references/nist-ai-600-1.md), [NIST SP 800-53 r5](references/nist-sp-800-53-r5.md), [OWASP LLM Top 10](references/owasp-llm-top-10.md), [OWASP ML Top 10](references/owasp-ml-top-10.md), [SR 11-7](references/sr-11-7.md)

## Playbooks

([index](playbooks/index.md))

* [Knowledge sources map](playbooks/knowledge-sources.md) - the librarian's scrape map.
* [Install and run AI-LinkMO](playbooks/install-and-run.md)
* [Bring your own data (BYOD)](playbooks/bring-your-own-data.md)

## Organizations

([index](org/index.md)): [FINOS](org/finos.md), [IBM](org/ibm.md)
