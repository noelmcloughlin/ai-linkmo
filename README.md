# AI-LinkMO: AI Linked Data Model Operate

> "Search out, to no one favour show; with heart that justice loves\
> Consult, then act; this is the rule that right approves."\
> — Thiruvalluvar, *Tirukkural* 541, *The Right Sceptre* (tr. G.U. Pope, 1886)

**Regulation in, auditable, queryable AI governance out.**

AI-LinkMO is a reference implementation of *operational* AI governance. It takes open AI-risk data and turns it from documents you *read* into linked data you can *query, integrate and automate against*. Its sources are IBM AI Atlas Nexus, the FINOS AI Governance Framework, NIST AI RMF, the EU AI Act, ISO/IEC 42001, the OWASP Top 10s and more: nine frameworks, each credited in [NOTICE](NOTICE).

The documentation is at [noelmcloughlin.github.io/ai-linkmo](https://noelmcloughlin.github.io/ai-linkmo/), with its [knowledge pages](https://noelmcloughlin.github.io/ai-linkmo/knowledge/). To run the demo, see [the quick start](https://noelmcloughlin.github.io/ai-linkmo/docs/install/#quick-start). [The architecture](https://noelmcloughlin.github.io/ai-linkmo/docs/architecture/) says why governance needs a catalogue, what the four doors (the CLI, the API, the web UI and the graph database) share, and where this sits.

> **Only want to ask?** Install `ktl-docent` into any agent you use, by a route from [the install page](https://w3id.org/ktl/docs/install/), and ask it about this project. It answers from the bundle and says how far each answer has been checked.
>
> **Agents:** if `.lokf/knowledge/index.md` exists, read it first. `llms.txt` says how to weigh it.

AI-LinkMO's family is [IBM AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/), which provides the AI Risk Ontology (a [LinkML](https://linkml.io/) schema) and the packaged risk data. Every door here is generated from that schema, and the architecture page says how the couplet above is the shape of the work.
