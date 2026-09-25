# AI-LinkMO: AI Linked Data Model Operate

> "Search out, to no one favour show; with heart that justice loves\
> Consult, then act; this is the rule that right approves."\
> — Thiruvalluvar, *Tirukkural* 541, *The Right Sceptre* (tr. G.U. Pope, 1886)

**Regulation in → auditable, queryable AI governance out.**

AI-LinkMO is a reference implementation of *operational* AI governance. It takes open AI-risk data and turns it from documents you *read* into linked data you can *query, integrate and automate against*. The sources are the [IBM AI Atlas Nexus ontology](https://ibm.github.io/ai-atlas-nexus/ontology/), the [FINOS AI Governance Framework](https://air-governance-framework.finos.org/), NIST AI RMF, the EU AI Act, ISO/IEC 42001, the OWASP Top 10s and more: nine frameworks, each credited in [NOTICE](NOTICE). **One linked model, four ways in: a risk identifier means the same thing in a terminal, a pipeline, a browser and a graph query.**

*Here to run it? Start at [Install](#install). Here to see what this adds to AI Atlas Nexus? Start at [Where this sits](#where-this-sits).*

<p align="center">
  <img src="byo/images/architecture.png" alt="Architecture: sources in, one linked model, four access patterns out" width="720" />
</p>

> **Prefer to ask?** Install the docent skill into any agent you already use (`npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-docent --yes`) and ask it about this project, such as *where the EU AI Act encoding comes from, and who checked it*. It answers from this repository's own bundle and says how far each answer has been checked. **Agents:** if `.lokf/knowledge/index.md` exists, read it first; `llms.txt` says how to weigh it.

## Why governance needs a catalogue

AI governance today mostly lives in PDFs and spreadsheets:

- **Frameworks multiply.** NIST AI RMF, the EU AI Act, ISO/IEC 42001, FINOS AIGF, the OWASP LLM Top 10, SR 11-7: each has its own vocabulary for overlapping risks and controls.
- **Mapping is manual.** *Which of our controls satisfy both NIST and the EU AI Act?* Today an analyst answers that with a crosswalk spreadsheet, built by hand, slow to make, and stale the moment a framework updates.
- **Governance and engineering don't share a language.** Compliance teams work in policy clauses; engineers work in pipelines and APIs. Nothing traces a regulatory obligation to a deployed control.

The knowledge already exists; it is in the frameworks. What is missing is the catalogue: one model in which a risk, a control and the clause that requires it are each one record with one identifier. Then the question above is a query rather than a quarter's work, and the answer is the same whoever asks it and however they ask.

## One model, four ways in

AI-LinkMO closes that gap with **one linked data model**, a LinkML ontology of risks, controls, obligations, taxonomies, models, evaluations and incidents, exposed through **four DevSecOps-ready access patterns**. Every stakeholder gets the same single source of truth in the form they can use:

| Access pattern | Who it serves | What you get |
| :--- | :--- | :--- |
| **Command Line Interface (CLI)** | Engineers, CI/CD pipelines | Automation-friendly queries and exports (fastCLI/slowCLI modes) |
| **FastAPI Backend** | System integrators, GRC tools | REST API as the single source of truth, aligned to [OpenAPI](lib/api/openapi.yaml) |
| **Svelte Web UI** | Risk, compliance and business stakeholders | Point-and-click exploration with persistent identifiers, no coding required |
| **Graph Database (Neo4j)** | Analysts, data scientists | Relationship analysis and regulatory crosswalks as a queryable graph |

Every door is generated from [the same ontology](https://ibm.github.io/ai-atlas-nexus/ontology/): the CLI, the API, the web UI and the schema. That is why a risk identifier means the same thing everywhere, and why the traceability is auditable. The couplet at the top is the shape of the work: *search out* the frameworks; show *no favour* among them, with one ontology and one identifier for each thing; *consult* them against each other, which is what a crosswalk is; *then act*, from a terminal, a pipeline, a browser or a graph query.

## What it looks like

- *"Show me every risk defined by NIST AI RMF"* → `./ai risk --isDefinedByTaxonomy nist-ai-rmf`
- *"Which controls mitigate toxic output?"* → `./ai control --related --hasRelatedRisk atlas-toxic-output`
- *"Map NIST risks to the FINOS framework"* → `./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod`
- *"Add our internal AI policy taxonomy alongside the public ones"* → drop a schema-compliant YAML file into [./byo/data](./byo/data) ([Bring your own data](#bring-your-own-data))
- *"Walk me through all four, with a real incident"* → [byo/notes/EXAMPLES.md](byo/notes/EXAMPLES.md), a scripted demo that traces a leaked-prompt incident to its risks and controls and ends in a CI gate

Screenshots of each door are in [byo/images/](byo/images/): the API starting, the web UI and its record viewer, curate mode, the CLI, a crosswalk, and the graph in Neo4j.

### Key concepts, in plain English

| Term | What it means |
| :--- | :--- |
| **Taxonomy** | A framework's catalogue of risks/controls (e.g. NIST AI RMF, FINOS AIGF) |
| **Risk** | A named, identified harm (e.g. `atlas-toxic-output`, `nist-confabulation`) |
| **Control / Action** | Something you do or deploy to detect or mitigate a risk |
| **Obligation** | A requirement a framework imposes, with evidence categories describing how you prove it |
| **Crosswalk** | A machine-generated mapping of equivalent concepts *between* frameworks |
| **Incident** | A realised risk, something that happened (e.g. `ibm-risk-atlas-ri-fake-legal-cases`), linked back to the risks it demonstrates |
| **Evaluation** | A benchmark or test that measures a risk or a capability (e.g. `ai_eval_PopQA`), linked to the datasets and tasks it uses |
| **BYOD** | Bring Your Own Data: your internal policies encoded in the same schema, queryable alongside the open data |

## Where this sits

AI-LinkMO's family is [IBM AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/). Upstream provides the AI Risk Ontology, a [LinkML](https://linkml.io/) schema; the packaged risk data; and the `ai-atlas-nexus` library that loads both. Every door here is generated from that schema. This repository is a workshop that runs over them. It adds doors, encodings and checks, and no ontology of its own. It adds no provenance on the records yet either: nothing says who checked an encoding against the framework's own text. [For the curious](docs/for-the-curious.md#where-this-sits) lists what is added and where, and says why the missing provenance is the auditor's first question.

## Install

Python 3.11+ and [uv](https://docs.astral.sh/uv/); Node 22 for the web UI.

```bash
uv sync --extra test
./ai --help
```

That is the offline CLI, ready to use. If `uv sync` needs to compile anything on your machine (an older `gcc`, a CUDA build, a corporate package index), or you have upgraded `ai-atlas-nexus` and need to regenerate the UI's schema, see [docs/install-notes.md](docs/install-notes.md).

## Quick start

1. **Start the API** ([details](lib/api/README.md)). It listens on port 8000, aligned to [the ontology](https://ibm.github.io/ai-atlas-nexus/ontology/) and to [OpenAPI](lib/api/openapi.yaml). Its write endpoints are not authenticated, so keep it on localhost.

   ```bash
   uv run uvicorn lib.api.server:app --reload
   ```

2. **Start the web UI** in a second terminal ([details](lib/frontend/README.md)). The login in the top corner is a persona picker for the demo, not authentication. **Curate mode**, which lets you add, edit and delete records in your own data files, sits behind it.

   ```bash
   cd lib/frontend
   npm ci
   npm run dev
   ```

3. **Try the CLI** in a third terminal ([details](lib/cli/README.md)). Every entity type is one command away; [docs/cli-examples.md](docs/cli-examples.md) lists them all.

   ```bash
   ./ai -h
   ./ai risk -h
   ```

## Working with the data

### Bring your own data

The open frameworks are the starting point. The value comes when your **internal** policies, taxonomies and controls live in the same model, so one query spans public regulation and private practice.

Add schema-compliant YAML files to [./byo/data](./byo/data); the [upstream readme](https://github.com/IBM/ai-atlas-nexus/blob/main/src/ai_atlas_nexus/ai_risk_ontology/util/README.md) says what the schema expects, and the nine encodings already there, [FINOS](./byo/data/finos-aigf.yaml) first, show the shape. Validate a contributed file against the schema:

```bash
SDIR="$(uv run python -c 'import ai_atlas_nexus, pathlib; print(pathlib.Path(ai_atlas_nexus.__file__).parent / "ai_risk_ontology" / "schema")')"
uv run linkml validate byo/data/*.yaml -s "${SDIR}/ai-risk-ontology.yaml"
```

### Crosswalk

A crosswalk is computed from the data, not kept by hand in a spreadsheet. That is where linked data pays off for a compliance team. The `./ai` command maps the risks in one taxonomy onto another, finds the related risks, and shows a subset of the risk content as a pandas dataframe:

```bash
./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod
```

### Graph database

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. One command exports the schema and the data as Cypher:

```bash
./ai graph cypher --export --byod
```

The export reads the packaged ontology, so it shows the open frameworks; `--byod` does not add your uploads to it ([Status and caveats](#status-and-caveats)). To load it into Neo4j in a container and look at it in the browser: [docs/neo4j.md](docs/neo4j.md).

## For the curious

The sections above are everything you need to run it. What the repository leaves out, provenance on the records; where it could go next, from policy documents to risks and from risks to provenance records; how to curate open data or build Python applications on the ontology; and how to run LLM inference or ARES with your own infrastructure: [docs/for-the-curious.md](docs/for-the-curious.md).

## Status and caveats

- **This is a demo.** The OpenAPI spec, the web UI and the CLI will all be reworked; treat their shapes as illustrative, not as a contract.
- **Keep it on localhost.** The write endpoints are unauthenticated, the web UI's login is a persona picker, and `graph/` is committed, regenerable output that the export commands rewrite in place. [SECURITY.md](SECURITY.md) lists each limitation and what is planned.
- **`--byod` does not reach the Cypher export.** `graph/cypher/export.py` reads the packaged ontology only, so the Neo4j walkthrough shows the open data, not your uploads.
- **Two encodings are thinner than their type suggests.** `byo/data/eu_ai_act.yaml` is a `RiskTaxonomy` of 308 requirement rows and no risks, so query it as `rule`, not `risk`; `ffiec_it_handbook.yaml` is a `RiskControlGroupTaxonomy` with groups and no controls.
- **No encoding has been checked by a named person against its framework's text.** Each header says which script produced it; the ontology has no field for a reviewer, and there has been none ([what it does not add yet](docs/for-the-curious.md#what-it-does-not-add-yet-provenance)).
- **Nobody has confirmed a bundle concept yet.** All 39 are *Checked by automation only*; `ktl-curator` is how a person changes that. The bundle's `base_iri` is also a placeholder; moving it to a namespace the project controls rewrites every `id`, and has waited for a decision since 2026-08-05.
- **Slow paths.** `--mode local` loads the ontology in-process on every call, and the full local-mode test sweep takes about 25 minutes. LLM inferencing needs a vLLM host you run; ARES needs an upstream pull request.

## Releases

No release has been cut yet; `pyproject.toml` says 0.1.0, matching the `v0.1.0` baseline tag. [`CHANGELOG.md`](CHANGELOG.md)'s `## [Unreleased]` section is written as changes happen, and [`semantic-release.yml`](.github/workflows/semantic-release.yml) does the rest on each merge to `main`: it computes the next version from Conventional Commits, promotes that section into a dated heading, bumps `pyproject.toml` and `uv.lock`, and publishes a GitHub Release from the same text, once a person approves it in the `release` Environment. Only `feat:`, `fix:` and `security:` cut a release. Once `KNOWLEDGE_RELEASE_ENABLED` is set, each release also carries the `.lokf/knowledge/` bundle as a zip, when it changed.

**The version stays below 1.0.0.** This is a demo, and the shapes above will change. The `v0.1.0` tag is a baseline, not a release: it stops semantic-release defaulting the first release to 1.0.0, and a breaking change bumps the minor version, not the major one. Reaching 1.0.0 will be a decision, not something a commit message can trigger. [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers) has the maintainer's steps.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup and the pre-PR checklist. Three toolchains live here: Python and uv at the root, Node in `lib/frontend/`, and a second uv project in `.lokf/`.

```text
ai                      the CLI entry point (runs lib/cli through uv)
lib/cli/                argparse generated from the OpenAPI spec; fastCLI (via the API) or slowCLI (offline)
lib/api/                FastAPI backend; openapi.yaml is the source of truth for every route
lib/frontend/           Svelte 5 web UI (Vite; proxies to the API on :8000)
lib/test/               pytest suite; its API-mode CLI cases are this README's examples, checked
graph/                  the exported ontology, crosswalk CSVs, and cypher/export.py for Neo4j
byo/data/               nine governance frameworks encoded for the AI Risk Ontology
byo/notes/EXAMPLES.md   a scripted walk through all four access patterns
docs/                   longer material moved out of this README
.lokf/                  the sidecar: this repository's own knowledge bundle (knowledge/) and its tooling
.github/workflows/      tests, lint, the knowledge-bundle gates, releases
```

The test suite runs 101 CLI cases in API mode and in local mode, and starts the API server for you. `uv run pytest lib/test -m "not slow"` is what CI runs, about two minutes; `./scripts/tests.sh` has the narrower modes. The web UI (`npm run check`, `npm run lint`, `npm test` in `lib/frontend/`) and the bundle (`cd .lokf && just lokf-validate`) have their own gates. [lib/test/README.md](lib/test/README.md) has the detail.

## This repository's own bundle

This repository keeps a LOKF bundle of its own under `.lokf/knowledge/`: documentation about AI-LinkMO, kept the way AI-LinkMO keeps governance data, with one identifier per concept and a source beside every claim. The [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder) skills maintain it, installed at run time by a scheduled [workflow](.github/workflows/knowledge-librarian.yaml). It is what the docent answers from, and none of it is part of the product. To contribute to it, [CONTRIBUTING.md](CONTRIBUTING.md#agent-skills-optional---only-for-editing-this-repos-own-lokf-bundle) says which skills that takes.

## Credits

- [IBM AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/): the [AI Risk Ontology](https://ibm.github.io/ai-atlas-nexus/ontology/) and open risk data every access pattern here is generated from, and the `ai-atlas-nexus` package that loads them.
- [FINOS AI Governance Framework](https://air-governance-framework.finos.org/): the first framework encoded under `byo/data/`, and the model for the eight that followed; every framework's authors are listed in [NOTICE](NOTICE).
- [Nolan Nichols](https://lokf.nolan-nichols.com/), creator of [LOKF](https://lokf.nolan-nichols.com/specification/) (Linked Open Knowledge Format) and its [toolkit](https://github.com/nicholsn/lokf).
- The [LinkML Community](https://linkml.io/), creators of [LinkML](https://linkml.io/linkml/), the schema language that both the AI Risk Ontology and LOKF are written in.
- [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder): the librarian that maintains this repository's own bundle, and the docent in the notice at the top.
- Thiruvalluvar, whose *Tirukkural* has been read on the duties of those who govern for some two thousand years; the couplet at the top is in G.U. Pope's 1886 translation.

## Contributing, security, license

[CONTRIBUTING.md](CONTRIBUTING.md) says how to contribute; participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md), and [AI_COVENANT.md](AI_COVENANT.md) sets out how AI-assisted contributions are handled. Read [SECURITY.md](SECURITY.md) before running the API outside localhost or enabling the BYOD upload path. Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
