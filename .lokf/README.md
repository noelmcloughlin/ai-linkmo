# `.lokf/`: AI-LinkMO's machine-readable knowledge base

This is a small **sidecar** that captures AI-LinkMO's own knowledge (its services, datasets, references, playbooks, glossary, explanations, and organizations) as plain Markdown files that are **also a queryable knowledge graph**. It does not touch the app build; it is independent tooling you can run on its own.

## The 60-second version

- **OKF (Open Knowledge Format)** is a folder of Markdown files, one *concept* per file, each with a little YAML frontmatter block (`type`, `title`, `description`, ...). They are just files you can read on GitHub or in any editor.
- **LOKF (Linked OKF)** gives every field a precise meaning (schema.org, DCAT, PROV-O), so the same Markdown turns into RDF and is queryable with SPARQL. The [`lokf`](https://pypi.org/project/lokf/) PyPI package is the toolkit that does the turning.

You write normal Markdown; you get a validated, queryable graph for free.

## What's in here

```text
.lokf/
|-- knowledge/            # the bundle: one Markdown file per concept
|   |-- index.md          # bundle metadata + table of contents (reserved)
|   |-- log.md            # change history (reserved)
|   |-- services/         # CLI, FastAPI backend, Svelte web UI, Neo4j graph database
|   |-- datasets/         # the knowledge-graph export, the NIST AI RMF crosswalks, and each framework's data
|   |-- references/       # the frameworks and standards the data comes from
|   |-- playbooks/        # knowledge sources, install and run, bring your own data
|   |-- glossary/         # BYOD, control action, crosswalk, obligation, risk, taxonomy
|   |-- explanations/     # why linked AI governance
|   |-- org/              # FINOS, IBM, the maintainer
|-- pyproject.toml        # declares the `lokf` toolkit as a dependency
|-- justfile              # convenience commands (below)
|-- scripts/              # the librarian wrapper, the preflight, the gate's two checks and the docent's feedback recorder
|-- m365/                 # the Microsoft 365 Copilot skills' instructions and their builder; the release workflow packs them
|-- queries.http          # SPARQL queries for the local endpoint (VS Code REST Client)
|-- curators/             # appears once a curator's public key is on file; who may confirm at the gate
|-- feedback.md           # appears once a reader's agent records a gap; input for the librarian, not knowledge
```

The `knowledge_bundle` link at the repository root is this same `knowledge/` directory under an ordinary, visible name. It is there for folder pickers and file managers that hide dot-directories, and, for Obsidian users, for "Open folder as vault": open the link *itself* as a vault, never the repository root, which cannot see a dot-folder or a link that resolves inside it. Git carries the link; a sync service does not, so `just lokf-link` recreates it on a machine where it is missing (Windows: `mklink /J knowledge_bundle .lokf\knowledge`). Every command below works without it.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/), the Python package runner.
- [`just`](https://just.systems/), optional, for the shortcut recipes.

## Use it

```bash
cd .lokf
just lokf-install    # one-time: install the toolkit (uv sync)
just lokf-validate   # check every concept against the LOKF schema
just lokf-serve      # local SPARQL endpoint + interactive graph explorer
just lokf-convert    # print the whole bundle as RDF (Turtle)
```

Without `just`:

```bash
cd .lokf
uv sync
uv run lokf validate knowledge
uv run lokf serve knowledge
uv run lokf convert knowledge --format ttl
```

## Add or edit a concept

1. Create a Markdown file under `knowledge/<kind>/` (e.g. `services/`, `metrics/`).
2. Start with frontmatter. OKF requires only `type`; this bundle also sets `id`, `title`, and `description` on every concept.
3. Link concepts with typed-relation keys whose values are target `id`s, such as `dependsOn:`, `about:`, `references:`, `measures:`. Run `uv run lokf vocab` to list available relations.
4. Add the concept to the table of contents in `knowledge/index.md`.
5. Run `just lokf-validate` before committing.

## Learn more

- LOKF specification & Golden Rules: <https://lokf.nolan-nichols.com/>
- `lokf` toolkit (PyPI): <https://pypi.org/project/lokf/>
- LOKF schema, if Python is not available, at the tag `pyproject.toml` floors: <https://github.com/nicholsn/lokf/blob/v0.8.0/lokf.yaml>
- OKF spec: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>
