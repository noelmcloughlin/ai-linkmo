# ai-risk-ontology-linkmo

A command line and an HTTP API over the `ai-risk-ontology` LinkML schema and its data. Both are built from the schema when they start: one command and one endpoint per exposed class, with one filter per slot of the class. Nothing is generated into this folder ahead of time, so a slot added to the schema is a filter at the next start.

The linkmo copier template made this project at ai-linkmo's root, which has no LinkML sidecar. It reads the schema from `pkg:ai_atlas_nexus/ai_risk_ontology/schema/ai-risk-ontology.yaml` and the records from `ai_linkmo.atlas:AtlasSource`, which asks ai-linkmo's `lib/api/handlers.py`: the DuckDB store or the ai-atlas-nexus library, with the related-risk lookups and the bring-your-own data.

## Use it

From the host root:

```bash
just --justfile ai-risk-ontology-linkmo/justfile install          # uv sync, once
just --justfile ai-risk-ontology-linkmo/justfile cli --help       # the command line, ai
just --justfile ai-risk-ontology-linkmo/justfile serve            # the API on http://localhost:8000/docs
just --justfile ai-risk-ontology-linkmo/justfile test
```

Inside this folder, plain `just <recipe>` works, and after `just install` so does `uv run ai --help`. `just --list` shows the rest: the published contract, a web UI's entity list, the SSSOM check, the Datasette browse database and the schema's pages with examples.

This project is a member of ai-linkmo's uv workspace. ai-linkmo's `uv sync` installs it, editable, beside ai-atlas-nexus, which the `pkg:` paths read, and `./ai` at the host root runs its command line. `just install` here adds the test tools to that environment and removes nothing. ai-linkmo's justfile runs these recipes on the same environment through `LINKMO_PYTHON`.

A command lists the records of its class. Give an identifier to fetch one record, any option to filter, `--count` for the number only, and `--mode api` to ask a running server instead of reading the data in the process. The API answers `GET /<class>` with the same parameters and the same JSON, and publishes its contract at `/openapi.json`.

## What is yours

The template created these files once and never overwrites them:

- `exposure.yaml` says which classes are exposed, under which path, and binds hand-written operations to paths.
- `src/ai_linkmo/hand.py` holds those operations.
- `tests/expected_counts.yaml` lists the questions your data must answer and how many records each returns.
- `project.justfile` holds your own recipes.

Everything else follows the template. Run `copier update -a .copier-answers.linkmo.yml --trust` from the host root to bring in a new version. It updates this template on its own and does not touch the sidecar.
