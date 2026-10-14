# AI-LinkMO: AI Linked Data Model Operate

> "Search out, to no one favour show; with heart that justice loves\
> Consult, then act; this is the rule that right approves."\
> — Thiruvalluvar, *Tirukkural* 541, *The Right Sceptre* (tr. G.U. Pope, 1886)

*Regulation in ==> auditable, queryable AI governance out.*

AI-LinkMO is a reference implementation of *operational* AI governance. It takes open AI-risk data and turns it from documents you *read* into linked data you can *query, integrate and automate against*. The sources are the [IBM AI Atlas Nexus ontology](https://ibm.github.io/ai-atlas-nexus/ontology/), the [FINOS AI Governance Framework](https://air-governance-framework.finos.org/), NIST AI RMF, the EU AI Act, ISO/IEC 42001, the OWASP Top 10s and more: nine frameworks, each credited in [NOTICE](NOTICE).

To run it, see [the quick start](docs/install.md#quick-start). [The architecture](docs/architecture.md) says why governance needs a catalogue, what the four doors share, and where this sits beside AI Atlas Nexus. This is a demo: keep it on localhost, since the write endpoints are unauthenticated, and [docs/status.md](docs/status.md) lists the caveats.

AI-LinkMO's family is [IBM AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/), which provides the AI Risk Ontology, a [LinkML](https://linkml.io/) schema, and the packaged risk data. Every door here is generated from that schema, and the architecture page says how the couplet above is the shape of the work.

> **Agents:** if `.lokf/knowledge/index.md` exists, read it first; `llms.txt` says how to weigh it.
