# For the curious: what this leaves out, and where it could go

[The README](../README.md) says everything you need to run AI-LinkMO. This page is for anyone who wants to go further: what this repository adds over its upstream and what it does not add yet, two roadmap directions, and how to build on the ontology or run the parts that need your own infrastructure.

## Where this sits

AI-LinkMO's family is [IBM AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/). Upstream provides three things:

- **The AI Risk Ontology**, a [LinkML](https://linkml.io/) schema of risks, controls, obligations, taxonomies, models, evaluations and incidents. Every CLI command, API route, UI form and graph label here is generated from it, which is why one identifier means the same thing at every door.
- **The packaged risk data**: the IBM AI Risk Atlas, the public taxonomies packaged with it, and the relationships between them. The related-risk, related-control and related-incident lookups, and so the crosswalk, walk those relationships through the `ai-atlas-nexus` library; the LLM inference path calls its risk identification.
- **The toolchain**: the library that loads the ontology and the data, and LinkML's generators, which produce the JSON Schema the web UI ships.

This repository is a workshop that runs over them. It adds doors, encodings and checks, and no ontology of its own:

| Added here | Where |
| :--- | :--- |
| Four doors onto one model: CLI, FastAPI, Svelte UI, Cypher export for Neo4j | `lib/cli/`, `lib/api/`, `lib/frontend/`, `graph/` |
| Nine governance frameworks encoded in the ontology's own classes, as bring-your-own-data examples | `byo/data/` |
| Crosswalks between two taxonomies, on screen and as files | `./ai crosswalk`, `graph/` |
| A scripted walk through all four doors, ending in a CI gate | `byo/notes/EXAMPLES.md` |
| Every CLI example run as a test, in API mode and in local mode | `lib/test/` |
| Curate mode: a person adds, edits or deletes records in their own files through the UI | `PUT /byo` |

## What it does not add yet: provenance

The records carry no provenance.

- Each file under `byo/data/` says in a header comment which script produced it and from which input. Every row carries the same `dateCreated`, the day the generator ran.
- Nothing says who checked an encoding against the framework's own text, from which edition, or when it should be checked again. The ontology has no field for it. For an auditor that is the first question, and for all nine frameworks the answer today is *nobody has checked this yet*.
- Curate mode has the same gap: a person edits a record, but the persona is not an identity, and the record keeps no trace of who.

Where provenance belongs, in the ontology or elsewhere, is the second roadmap item below.

## Roadmap: automated policy-to-risk mapping

[asago policy mapper](https://github.com/asago-ai/asago-policy-mapper), part of [asago.ai](https://asago.ai/), an open-source AI safety and governance orchestrator, closes the semantic gap from the other direction. It reads unstructured corporate policy documents and extracts standardized risk identifiers, from *"the model must not provide medical advice"* to `atlas-hallucination` and `nist-ms-2.5`. It would complete the loop if it ran upstream of AI-LinkMO, **policy document → extracted risks → linked model → crosswalks, controls and evidence**: traceability from policy clause to deployed control.

## Roadmap: provenance on governance records

The AI Risk Ontology says what a risk, a control or an obligation *is*. It does not yet say what a provenance record looks like: who encoded a record, from which edition of a framework, who confirmed it, when to look again. Nor does it say what an AI step did at run time. [finos/fluxnova-ai#40](https://github.com/finos/fluxnova-ai/issues/40) sketches the second kind: context records for agents, models, tools and datasets, and runtime records for model invocations, tool calls and evaluation results, aligned to W3C PROV.

The first kind could land in three places: in the ontology; in the [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md), whose v0.2 defines `generated`, `verified`, `status` and `stale_after` for documents, and an *attested computation* for a tool's receipted result; or in a project such as [asago.ai](https://asago.ai/). That is something to investigate, not something this page decides.

## Curate your own open data

Open data is curated the way open source is: in public, by a community, one contribution at a time, and the datasets, benchmarks and mitigations here are open to that. Learn the basics of [LinkML](https://linkml.io/linkml/intro/overview.html) and its metamodel before you curate the model. It comes with a controlled vocabulary of terms, and a few basic components go a long way.

## Build Python applications on it

The [Python Reference](https://ibm.github.io/ai-atlas-nexus/reference/library_reference/) and the `SchemaView` class in the linkml-runtime let you introspect and manipulate the schema in code ([documentation](https://ibm.github.io/ai-atlas-nexus/examples/notebooks/schema_viewer/)). `./ai schemaview --introspect` is the CLI's window onto the same thing.

## Infer risk dimensions with an LLM, or evaluate with ARES

Both need infrastructure you run yourself: [llm-inferencing.md](llm-inferencing.md).

## Research

- [Pathways to Open Data, Linux Foundation](https://www.linuxfoundation.org/hubfs/LF%20Research/WOIC_ChallengeSession2024_Report_032525.pdf).
