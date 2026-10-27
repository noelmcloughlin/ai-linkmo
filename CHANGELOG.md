# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The `v0.1.0` tag is a baseline, not a release: it marks where versioning starts, so the first release was `0.2.0` rather than `1.0.0`. AI-LinkMO is a demo and stays below 1.0.0 deliberately - a breaking change bumps the minor version here. See [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers).

## [Unreleased]

### Changed

- **`./ai` runs the linkmo project's command line, and `lib/cli/` is gone.** It still asks the API by default, through `AI_LINKMO_MODE`. It prints plain JSON, indented on a terminal, with errors on stderr, and no longer probes other ports or takes `--verbose`.
- **`AI_ATLAS_API_URL` is now `AI_LINKMO_API_URL`**, and its opt-in is `AI_LINKMO_API_URL_ALLOW_REMOTE`. `0.0.0.0` no longer counts as a local host.
- **The linkmo project is a uv workspace member**, so `uv sync` installs it and nothing puts its `src/` on the path.

### Added

- **`just build-browse-byod` and `just browse-byod`** build and serve a browse database with the bring-your-own data, as 0.2.0 did.

### Fixed

- **An id with `byod` fetches one record again**: `/taxonomy?id=nist-ai-rmf&byod=true` answers `{"item"}`, as in 0.2.0.

## [0.5.0] - 2026-10-27

### Changed

- **The linkmo template serves the API, the CLI's commands and the browse build.** Its project in `ai-risk-ontology-linkmo/` replaces `lib/api/api.yaml`, the API kernel and `lib/browse/`, and answers every listing through `lib/api/handlers.py`, so the related-risk lookups and `byod` work as before.
- **`AI_LINKMO_DATA_SOURCE` is now `AI_LINKMO_BACKEND`**, with the same values, because the template's settings use the old name.
- **The web UI's entity list calls each Container slot `collection`**, the template's name, instead of `byo`.
- **Responses change in three places.** Records leave empty slots out instead of writing `null`, `/version` reports the schema and the datamodel instead of ai-atlas-nexus and the git commit, and the hand paths' operation ids are `hand.*`.

### Removed

- **The browse database of the bring-your-own data.** `just build-browse` writes one database, of the packaged data, under `ai-risk-ontology-linkmo/browse`.

## [0.4.15] - 2026-10-27

### Fixed

- **A `!` after the type marks a breaking change.** `.releaserc.json` names the Conventional Commits preset, so a `feat!:` commit bumps the minor version instead of releasing nothing.

## [0.4.14] - 2026-10-27

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.56.2](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/v0.56.1...v0.56.2).** The release changed `.lokf/.gitignore` here.

## [0.4.13] - 2026-10-26

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.56.1](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/v0.55.2...v0.56.1).** The release changed `.github/workflows/knowledge-registrar.yaml`, `.github/workflows/knowledge-librarian.yaml`, `.github/workflows/knowledge-release.yaml`, `.lokf/scripts/knowledge-preflight.sh`, `.lokf/scripts/knowledge-sync.sh`, `website/astro.config.mjs`, `website/scripts/check-links.mjs`, `website/scripts/config.mjs`, `website/scripts/markdown-ktl.mjs`, `website/scripts/raw-html.mjs`, `website/scripts/routes.mjs`, `website/scripts/sync.mjs`, `website/src/components/ConceptCard.astro`, `website/src/components/ConceptPreviews.astro`, `website/src/components/KnowledgeGraph.astro`, `website/src/components/Mermaid.astro`, `website/src/components/Neighbourhood.astro`, `website/src/components/TrustChart.astro`, `website/src/content.config.ts`, `website/src/pages/og/[...route].ts`, `website/src/styles/catalogue.css` and `.github/workflows/knowledge-website.yaml` here.

## [0.4.12] - 2026-10-23

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.55.2](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/d5c7817f57ac4e68cd48721a309825afaacd8994...v0.55.2).** The release changed `.github/workflows/knowledge-registrar.yaml`, `.github/workflows/knowledge-release.yaml`, `.github/workflows/knowledge-sync.yaml`, `.lokf/scripts/knowledge-librarian.sh`, `.lokf/scripts/knowledge-conventions.sh`, `.lokf/scripts/knowledge-conventions.py`, `.lokf/scripts/knowledge-preflight.sh`, `.lokf/scripts/knowledge-provenance.sh`, `.lokf/scripts/knowledge-feedback.sh`, `.lokf/scripts/knowledge-apply.sh`, `.lokf/scripts/knowledge-apply.py`, `.lokf/scripts/knowledge-report.sh`, `.lokf/scripts/knowledge-sync.sh`, `.lokf/.gitignore`, `.lokf/justfile`, `website/package-lock.json`, `website/package.json` and `website/src/components/KnowledgeGraph.astro` here.

## [0.4.11] - 2026-10-21

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.53.0](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/2801e26f2fc99675eb395b639670ec789e49eb08...d5c7817f57ac4e68cd48721a309825afaacd8994).** The release changed `.github/workflows/knowledge-librarian.yaml`, `.github/workflows/knowledge-sync.yaml`, `.github/PULL_REQUEST_TEMPLATE/knowledge-sync.md`, `.lokf/scripts/knowledge-librarian.sh`, `.lokf/scripts/knowledge-apply.py`, `.lokf/scripts/knowledge-sync.sh`, `.lokf/.gitignore`, `website/scripts/config.mjs`, `website/scripts/markdown-ktl.mjs`, `website/scripts/sync.mjs`, `website/src/components/KnowledgeGraph.astro`, `website/src/pages/graph.astro`, `.github/workflows/knowledge-website.yaml` and `website/scripts/raw-html.mjs` here.

## [0.4.10] - 2026-10-19

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.52.0](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/b7d15e5c58554d6af4b71dfe35ef2a6bfe8c45d8...2801e26f2fc99675eb395b639670ec789e49eb08).** The release changed `.github/workflows/knowledge-registrar.yaml`, `.github/PULL_REQUEST_TEMPLATE/knowledge-sync.md`, `.lokf/scripts/knowledge-conventions.sh`, `.lokf/scripts/knowledge-conventions.py`, `.lokf/scripts/knowledge-preflight.sh`, `.lokf/scripts/knowledge-report.sh` and `.lokf/scripts/knowledge-sync.sh` here.

## [0.4.9] - 2026-10-17

### Security

- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [v0.47.0](https://github.com/noelmcloughlin/knowledge-trust-ladder/compare/13f847f1988ec1a7f1c41f63cc3f1945c2010231...b7d15e5c58554d6af4b71dfe35ef2a6bfe8c45d8).** The release changed `.lokf/scripts/knowledge-preflight.sh`, `.github/workflows/knowledge-sync.yaml`, `.github/PULL_REQUEST_TEMPLATE/knowledge-sync.md` and `.lokf/scripts/knowledge-sync.sh` here.

## [0.4.8] - 2026-10-17

### Security

- **The sidecar copies and the skills pin match `v0.46.0`.** The release changed `.github/workflows/knowledge-release.yaml`, `.lokf/scripts/knowledge-federate.py`, `website/package-lock.json` and `website/package.json` here; its [changelog](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/13f847f1988ec1a7f1c41f63cc3f1945c2010231/CHANGELOG.md) says how.

## [0.4.7] - 2026-10-17

### Security

- **The sidecar copies and the skills pin match `v0.45.1`.** The release changed `.lokf/scripts/knowledge-apply.py` and `.lokf/scripts/knowledge-federate.py` here; its [changelog](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/d38e52b20d99c21ff201be9252a01b1da28fff57/CHANGELOG.md) says how.

## [0.4.6] - 2026-10-16

### Security

- **The sidecar copies and the skills pin match `v0.45.0`.** The release changed `.lokf/scripts/knowledge-report.sh`, `.lokf/m365/ktl-docent-m365.md`, `website/scripts/sync.mjs`, `website/src/components/ConceptCard.astro`, `website/src/content.config.ts` and `website/src/styles/catalogue.css` here; its [changelog](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/08c13b5e30a6e0c4c6a2373658ee2c3ebbf4ae8e/CHANGELOG.md) says how.

## [0.4.5] - 2026-10-16

### Security

- **The sidecar's toolkit lock takes the patched PyJWT, urllib3, httpx2, httpcore2 and mcp.** It closes the open security alerts on `.lokf/uv.lock`, apart from one PyJWT advisory that has no fixed release yet. The app's own dependencies are unchanged.

## [0.4.4] - 2026-10-16

### Security

- **The sidecar copies, the website's copies and the skills pin match `v0.44.0`.** The site's link check ends an address at a backtick, so an address in a code span no longer fails the build, and the site takes mermaid 12.2.

## [0.4.3] - 2026-10-15

### Changed

- **The README links the website.** It names the site and its knowledge pages, and the quick start, the architecture page and the status page open there rather than as Markdown files on GitHub. No application change.

## [0.4.2] - 2026-10-15

### Security

- **The website's copies and the skills pin match `v0.43.0`.** The site serves the whole bundle as `llms-full.txt`, the bundle log as an Atom feed, and each docs page as Markdown beside it. A concept page links its history and licence and opens the knowledge graph on the concept, and a link to a concept previews it on hover and on focus. A release page links the repository, the docs and the bundle at the release's tag, and a page and its retelling offer each other as reading levels. No application change.

## [0.4.1] - 2026-10-14

### Security

- **The sidecar copies, the website's copies and the skills pin match `v0.42.0`.** Conventions rule 13 no longer reads a move of the bundle's `base_iri` as an edit of every confirmed concept, and a data page opens Datasette Lite in a new tab. No application change.

## [0.4.0] - 2026-10-14

### Added

- **The website serves the data to browse in Datasette Lite.** The two databases `just build-browse` writes sit under *Browse the data*, and the site's build runs the recipe. No application change.

## [0.3.2] - 2026-10-14

### Security

- **The sidecar copies, the website's copies and the skills pin match `v0.41.0`.** The scheduled librarian takes an agent that wants its prompt somewhere other than after `-p`, named by the repository variable `AGENT_PROMPT_FLAG`. It writes its patch with the agent's own file tool, so an agent refused a shell write no longer gives up. Both came with the `v0.40.0` copies, which 0.3.1 included without an entry. The website's copies show the schema's pages under a Schema topic and draw their class diagrams, and its workflow also runs weekly and on a change to a justfile, a `pyproject.toml` or a `uv.lock`. No application change.

## [0.3.1] - 2026-10-14

### Changed

- **Four docs pages lose their dead sentences.** The crosswalk, graph, contribution and status paragraphs say the fact and stop. No application change.

## [0.3.0] - 2026-10-14

### Added

- **A website for the knowledge bundle, in `website/`, laid down by the ktl-website skill.** Each concept has a page with its trust label, beside a health page, the knowledge graph and search by trust and type. The four files `lokf export` writes are served under `/knowledge/`, and the README, the docs pages and this changelog become pages too. `knowledge-website.yaml` builds it on every pull request and publishes it to GitHub Pages once `KNOWLEDGE_WEBSITE_ENABLED` is `true`.

### Changed

- **The README is a doorway, in the style of Knowledge Trust Ladder's.** It keeps the couplet, the tagline, the opening paragraph and the agents note, and links the quick start, the architecture page and the caveats. The catalogue story, the four doors, where the project sits and the credits moved to `docs/architecture.md`, and the install and quick start steps to `docs/install.md`. No application change.

## [0.2.2] - 2026-10-14

### Security

- **The sidecar copies and the skills pin match `v0.39.0`.** The preflight looks for ktl-website among the installed skills. The librarian and release workflows say their variables go under Repository variables, never on an environment, which neither job can read, and the scheduled librarian installs a ktl-librarian whose setup page says the same. No application change.

## [0.2.1] - 2026-10-13

### Security

- **The sidecar copies and the skills pin match `v0.38.2`.** The registrar, librarian and release workflows run the justfile's `lokf-check-refs` recipe, and their actions move to newer pinned releases. The docent's Copilot instructions prefer a retelling for a younger reader, and give the adult concept's label with it. The pen no longer adds a second "edited since" note to a log line that already has one. The scheduled librarian installs a ktl-librarian that retells a confirmed concept for younger readers when the curation policy declares a band. No application change.

## [0.2.0] - 2026-10-10

### Changed

- **The CLI and the API are generated from the schema, not from a hand-written OpenAPI file.** `lib/api/api.yaml` names the 22 exposed classes and the six hand paths; every slot of a class is a filter, an enum slot offers its values, and `lib/test/test_cli_api_identity.py` proves both doors expose the same surface. The contract is the server's `/openapi.json`, written to `docs/openapi.json` by `just gen-openapi` and served by Scalar at `/scalar` too.
- **A scope lists every instance of its class, wherever the data file put it.** `control` is every RiskControl including the Actions (1,102), `model` every LargeLanguageModel including the Adapters (58), `requirement` the Requirements alone (51), and `group` every Group subclass (183). The expected counts follow ai-atlas-nexus 1.2.5, which is now the minimum.
- **The web UI's entity list is generated.** `just gen-ui-config` writes `entities.json` from the exposure file, so a UI key is an API route by construction; labels, groups and filters stay a hand-written overlay, and eleven filters that were not slots of their class are gone.
- **The web UI's record form is generated from the JSON Schema.** `RecordForm.svelte` renders the endpoint's class with @sjsf and its daisyUI 5 theme and checks it with ajv before saving, while the taxonomy file, the stamped dates and the read-only class designator work as before. `app.css` now loads daisyUI for the components the form uses, so the existing `btn` and `input` classes in the pagination and the filter panel take daisyUI's styles too.
- **The Cypher export is fetched, not generated.** `just fetch-cypher` downloads the export ai-atlas-nexus commits at the installed version's tag, with a provenance header; `--byod` with it is refused, since that artefact holds the packaged data only.

### Added

- **A DuckDB store behind the listings.** `just load-store` loads the data through linkml-store, one collection per concrete class, in about fifteen seconds; the listings read it when `AI_LINKMO_DATA_SOURCE` is `store`, or by default once it exists, and `lib/test/test_data_source.py` shows the store and the library answer alike. `just validate-store` reads linkml-store's findings rather than its exit code, and CI runs it with the 30 upstream data findings as the ceiling. `just index-store` builds a trigram index, `GET /search` and `./ai search` query it, and `just dump-store` writes the store as YAML.
- **A browse UI over the data.** `just build-browse` builds two SQLite databases from the schema's `gen-sqltables` tables, with each record in its class's table and every ancestor's so that a reference to an abstract parent resolves, and Datasette metadata generated from the schema. `just browse` serves them with Datasette on port 8001.
- **Class pages with an example from the data.** `just gen-doc` writes the schema's pages with `gen-doc`, and each concrete class that has records shows the record whose identifier sorts first, validated against its class by `just gen-examples`.

### Removed

- `lib/api/openapi.yaml`, `server_dynamic.py`, the 22 per-class handlers, `validate_handlers.py`, `graph/cypher/export.py`, the committed Cypher file, and the `cymple` dependency.

## [0.1.9] - 2026-10-07

### Security

- **The sidecar copies and the skills pin match `v0.37.1`.** The provenance gate reads a `verified` or `generated` event that spans lines, or that sits behind a byte order mark or CRLF line endings, so a forged confirmation cannot hide in either. The unattended check follows a renamed concept. The pen refuses a provenance key in any letter case, and keeps a curator's send-back. The report reads every timestamp and event layout, names a retired concept's successor, marks a concept a reader disputed, and counts reliance through all thirteen relation fields. Conventions rule 14 refuses a commit that records a person's confirmation and also changes what the concept says.

## [0.1.8] - 2026-10-05

### Security

- **The sidecar copies and the skills pin match `v0.34.2`.** The preflight reads the CI variables by indirect expansion rather than `eval`, so a scanner that searches for `eval` finds none, and its output is unchanged. When `knowledge-feedback.sh` or `knowledge-report.sh` is missing, it names ktl-curator and an earlier ktl-docent as the skills that need it, since ktl-docent now runs its own copies. The scheduled librarian installs a ktl-librarian that reads LOKF's schema from a commit rather than a tag (Snyk W012). No application change.

## [0.1.7] - 2026-10-05

### Security

- **The sidecar copies and the skills pin match `v0.34.1`.** The Copilot docent's instructions, `.lokf/m365/ktl-docent-m365.md`, label a concept as the report script does. A retired concept carries no other label, *edited since a person last confirmed it* takes the place of *confirmed by a person*, and an empty `verified` list reads as *nobody has checked this yet*. A Miss in its gap report starts with the reader's question and says whether a concept looked relevant from `index.md`. No application change.

## [0.1.6] - 2026-10-05

### Security

- **The sidecar copies and the skills pin match `v0.34.0`.** The pin names the tag's commit too, in `TRUST_LADDER_SKILLS_SHA`, and the librarian's install step installs nothing unless the tag still names that commit. The librarian workflow has a third job, `earlier`, which reads the workflow's earlier pull requests under a token that reads pull requests and nothing else. A scheduled run then opens no second pull request beside an open one, and does not propose again what a person declined. The pen refuses a patch that would change a person's record, and writes each frontmatter value back as the file held it. The registrar gate and the release workflow install the toolkit with `uv sync --locked`, and the conventions script and the pen pin PyYAML. A week is quiet again once the librarian has asked about a source it cannot act on.

  `SECURITY.md` describes the three jobs and the two pin values, and `CONTRIBUTING.md` says the two move together and no longer says the librarian workflow carries local changes. No application change.

## [0.1.5] - 2026-10-05

### Changed

- **The README is a front door, with its detail in `docs/`**. Seven pages hold what moved out, from key concepts and working with the data to status, releasing, layout, Neo4j and for-the-curious, and a Read on table links them.
- **The sidecar has its `knowledge_bundle` doorway**, a link to `.lokf/knowledge` at the root, and the linters skip it. `.lokf/.gitignore`, `justfile` and `queries.http` catch up with the current templates: Obsidian's workspace folder is ignored, `just lokf-link` restores the doorway, and two queries list the concepts nobody has confirmed and those past review.

### Security

- **The sidecar copies and the skills pin match `v0.33.0`.** The scheduled librarian's one output is now `.lokf/patch.yaml`. `knowledge-apply.sh`, new here, checks every operation in it and writes the bundle, and keeps an index in the shape a person gave it. `publish` reads each person's event and note off the patched tree before it pushes, and the registrar gate asks the person behind a confirmation that a change removes, as it asks the one behind a confirmation it adds. `knowledge-report.sh`, also new, computes the health line and the record changes the pull request carries. A scheduled week with nothing waiting runs no agent, though a month's first week always does. A handled feedback entry moves to `.lokf/questions.md`, and the librarian's hand-off reaches the pull request in a code block. Release assets take their name from `KNOWLEDGE_RELEASE_NAME` when it is set, and a retrieval score runs only once `KNOWLEDGE_RETRIEVAL` is `true`.

  Conventions rule 12 holds an index bullet equal to its concept's title and description, so the apply script's `reindex` operation re-derived the bullets of the 23 concepts here that had drifted, in place of the short summaries the indexes carried. Rule 13 fails a change to a confirmed concept that does not move its `generated` stamp past the confirmation. The scripts' comments read plainer. `.lokf/.gitignore` ignores the patch file, `.lokf/README.md` names the new scripts and `questions.md`, and `SECURITY.md` names the new path and checks. No application change.

## [0.1.4] - 2026-09-24

### Security

- **Releases carry the docent as a Microsoft 365 Copilot skill.** The new `.lokf/m365/`, copied from the `v0.27.0` templates, holds its instructions, `ktl-docent-m365.md`, and `knowledge-m365.sh`, which builds it from a snapshot of the bundle. `knowledge-release.yaml` attaches it as `ktl-docent-m365-<tag>-<repository>.zip` beside the bundle zip; without the folder it attached the bundle alone. `CONTRIBUTING.md` and `SECURITY.md` count `.lokf/m365/` among the copies that move with the pin.

### Fixed

- **0.1.3 installed the librarian skill from `v0.27.0` and carried its copies**, not `v0.26.0` as its entry says. The entry was written before the sync moved the pin.

## [0.1.3] - 2026-09-24

### Fixed

- **The scheduled librarian installs its skill from `v0.26.0`.** The old pin, `v0.19.7`, has no `skills/ktl-librarian`, so every weekly run failed.

### Security

- **The sidecar copies match the `v0.26.0` templates.** `knowledge-feedback.sh` lets ktl-docent record a reader's gap without opening `feedback.md` (Snyk W011). `knowledge-release.yaml` attaches the bundle zip to a release, dispatched by the release job once `KNOWLEDGE_RELEASE_ENABLED` is `true`. The librarian hands its agent one credential, under the name `AGENT_API_KEY_ENV` gives, and validates with `--check-refs` before opening a pull request. Conventions rule 11 rejects an `at:` later than the commit that recorded it, and a bundle path with a byte above 0x7f is read rather than skipped.

## [0.1.2] - 2026-09-23

### Changed

- **This repository follows the skills repository's renames.** `lokf-agent-skills` is now `knowledge-trust-ladder` (a third-party repository named after the format read as LOKF's official home), and its skills and plugins carry the `ktl-` prefix. Every link, both `npx skills add` lines, the librarian workflow, the sidecar scripts and the `TRUST_LADDER_SKILLS_REPO`/`TRUST_LADDER_SKILLS_REF` variables (formerly `LOKF_SKILLS_*`) follow; GitHub redirects the old paths. The workflow's pin must move to the first skills release that carries the new names.
- **The scheduled librarian installs `v0.19.7`**, up from `v0.19.2`, so it runs the current skill rather than one five releases behind.
- **The signing-guide link pointed at a heading that no longer exists** (`CONTRIBUTING.md#signing-your-commits`); the guide has its own page now, `docs/signing-commits.md`.
- **The README, docs, CONTRIBUTING and workflow comments are restyled for the reader**: shorter sentences and plain statements; `docs/cli-examples.md` as headed code blocks with its recurring flags glossed; CONTRIBUTING back under its word budget, with the release rationale linked to the README.

## [0.1.1] - 2026-09-18

### Fixed

- **Retitling a pull request re-runs the release checks.** The title check told the author to retitle, but the workflow listened only for the default pull-request types, so a title change fired nothing and the check stayed red whatever the author did. The trigger now names `edited`.

### Security

- **The sidecar's scheduled-agent wrapper restores `.git/config` and `.git/hooks/` on every exit.** The copy here predated the `EXIT` trap, so an agent that poisoned `core.hooksPath` and then failed, or a cancelled job, left it for the workflow's later steps to read.
- **The registrar gate reads a confirmation whole, not its `by:` line.** Re-dating an existing `human:` event, moving its `revision` or writing it in flow style added no `by: human:` line and so passed the old gate unseen. The gate also refuses a `human:` id it cannot look up, resolves a commit-shaped `revision` against the tree, and now runs under a top-level `permissions: {}` with no checkout credential on disk.

### Added

- **The bundle gets the conventions gate it never had**, `knowledge-conventions.sh` and its Python half, checking the ten rules `lokf validate` cannot see. The sidecar also gains `knowledge-preflight.sh`, `knowledge-provenance.sh` and `.lokf/.gitattributes`, keeping the bundle on LF so a Windows checkout gives CI's verdict.
- **A pull request that would release is held to its release notes and its title.** The `plan` job refuses an empty `## [Unreleased]`, which semantic-release itself skips on a pull-request event, and refuses a title with no releasing type, since a squash merge takes its commit subject from the title.

- **Semantic release.** The version is computed from Conventional Commits on `main`; this file's `## [Unreleased]` section is promoted into a dated heading and used as the release notes, `pyproject.toml` and `uv.lock` are bumped to match, and a GitHub Release is published from it - behind the `release` Environment, so a person approves each one.
- `SECURITY.md`: the reporting route, and what the unauthenticated write endpoints do and do not promise.
