# Change Log

## 2026-10-27

* **Changed**: the source map's exclusions name `docs/threat-model.md` and `.github/workflows/lint-and-docs.yaml`, both added in #123, so every tracked file keeps a place in the map.

## 2026-10-18

* **Changed**: the source map names the three generator scripts beside the rows they serve, the sync's pull request template beside the sidecar, and the repository plumbing and `llms.txt` it leaves out, so every tracked file has a place in it.

## 2026-10-17

* **Changed**: EU AI Act requirements dataset lists `byo/data/eu_ai_act.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: FFIEC IT Handbook dataset lists `byo/data/ffiec_it_handbook.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: FINOS AI Governance Framework dataset lists `byo/data/finos-aigf.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: ISO/IEC 42001 controls dataset lists `byo/data/iso_42001.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: Knowledge-graph export (YAML + Cypher) lists `graph` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: NIST AI 600-1 GenAI profile dataset lists `byo/data/nist_ai_600_1.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: NIST AI RMF crosswalks lists `graph` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: NIST SP 800-53 r5 controls dataset lists `byo/data/nist_sp_800_53_r5.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: OWASP Top 10 for LLM Applications dataset lists `byo/data/owasp_llm_top_10.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: OWASP ML Security Top 10 dataset lists `byo/data/owasp_ml_top_10.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: DuckDB record store lists `lib/store` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: SR 11-7 model risk management dataset lists `byo/data/sr_11_7.yaml` under `sources`, so the work list compares it; `resource` keeps its URL, because `lokf export` reads a relative `resource` as a concept id.
* **Changed**: the `resource` of Risk is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Obligation is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Taxonomy is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Evaluation is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Control / Action is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Incident is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Bring Your Own Data is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Crosswalk is now the repository path `docs/key-concepts.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Neo4j Graph Database is now the repository path `graph`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of AI-LinkMO CLI is now the repository path `lib/cli`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of FastAPI Backend is now the repository path `lib/api`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Datasette browse UI is now the repository path `lib/browse`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` of Svelte Web UI is now the repository path `lib/frontend`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` and the 2 `sources` entries of Why linked AI governance are now repository paths, `docs/architecture.md` first, in place of GitHub addresses, so the work list sees when they move.
* **Changed**: the `resource` and the 3 `sources` entries of What AI-LinkMO adds to AI Atlas Nexus are now repository paths, `docs/for-the-curious.md` first, in place of GitHub addresses, so the work list sees when they move.
* **Changed**: the `resource` of Bring your own data (BYOD) is now the repository path `docs/working-with-the-data.md`, in place of its GitHub address, so the work list sees when it moves.
* **Changed**: the `resource` and the 7 `sources` entries of Install and run AI-LinkMO are now repository paths, `docs/install.md` first, in place of GitHub addresses, so the work list sees when they move.
* **Changed**: the `sources` entry of DuckDB record store is now the repository path `docs/working-with-the-data.md`, in place of its GitHub address, so the work list sees when it moves. Its `resource` keeps the GitHub address, since `lokf export` reads a path there as a concept id when it writes `datasets.jsonld`.
* **Provenance**: FINOS AI Governance Framework dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/finos-aigf.yaml` and needed no change.
* **Provenance**: ISO/IEC 42001 controls dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/iso_42001.yaml` and needed no change.
* **Provenance**: NIST AI 600-1 GenAI profile dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/nist_ai_600_1.yaml` and needed no change.
* **Provenance**: NIST SP 800-53 r5 controls dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/nist_sp_800_53_r5.yaml` and needed no change.
* **Provenance**: OWASP Top 10 for LLM Applications dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/owasp_llm_top_10.yaml` and needed no change.
* **Provenance**: OWASP ML Security Top 10 dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/owasp_ml_top_10.yaml` and needed no change.
* **Provenance**: SR 11-7 model risk management dataset, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `byo/data/sr_11_7.yaml` and needed no change.
* **Provenance**: NIST AI Risk Management Framework, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against its NIST page and the crosswalk files and needed no change.
* **Provenance**: NIST AI 600-1 (Generative AI Profile), which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the publication its DOI resolves to and needed no change.
* **Provenance**: NIST SP 800-53 Revision 5, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the publication its DOI resolves to and needed no change.
* **Provenance**: OWASP Top 10 for LLM Applications, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against genai.owasp.org and needed no change.
* **Provenance**: FINOS AI Governance Framework, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the framework's site and `byo/data/finos-aigf.yaml` and needed no change.
* **Provenance**: EU Artificial Intelligence Act, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the AI Act Explorer and `byo/data/eu_ai_act.yaml` and needed no change.
* **Provenance**: ISO/IEC 42001, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the Internet Archive's copy of its ISO page from 2026-10-06, since iso.org refuses automated reads, and needed no change.
* **Provenance**: FFIEC IT Examination Handbook, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the Internet Archive's copy of the handbook's home page from 2026-05-12, since the site refuses automated reads, and needed no change.
* **Provenance**: The FINOS concept, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against finos.org and the `byo/data/` file headers and needed no change.
* **Provenance**: The IBM concept, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against the ai-atlas-nexus site and `pyproject.toml` and needed no change.
* **Provenance**: The Noel McLoughlin concept, which a librarian run created on 2026-08-05, now has a `generated` record in place of the OKF v0.1 `timestamp`. It was re-read today against `pyproject.toml`, `LICENSE` and the GitHub profile and needed no change.
* **Changed**: NIST AI RMF crosswalks says the IBM Risk Atlas file names its mapping columns `closeMatch` and the like, as its header row does. The `fields` list matches the other two files only. The concept, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`.
* **Changed**: AI Risk Ontology names the two views its source names, an AI risk view and an AI model view, where it said a System view and a Risk view. The concept, which the librarian wrote at the bootstrap on 2026-07-13, now has a `generated` record in place of the OKF v0.1 `timestamp`.
* **Open question**: OWASP ML Security Top 10: <https://owasp.org/www-project-machine-learning-security-top-10/> now redirects to <https://owasp.org/projects/machine-learning-security-top-10>, which answers 404 (checked 2026-10-17). The project page is at <https://owasp.org/projects/machine-learning-security-top-ten>. `byo/data/owasp_ml_top_10.yaml` still cites the first address, and the source map asks that the two match. Which address should this reference cite?

## 2026-10-16

* **Prose**: reworded 17 concept bodies in plain English. No fact, link, number or frontmatter changed.
* **Changed**: What AI-LinkMO adds names what the library loads, which the earlier change today had left two sentences away.
* **Changed**: BYOD no longer says every access pattern picks up your files. The Cypher export refuses `--byod`, as `docs/neo4j.md` and `docs/working-with-the-data.md` say.
* **Changed**: Why linked AI governance gets a description that names the four doors, as the README and the architecture page now do, and cites both pages it draws on.
* **Changed**: Taxonomy says a catalogue of risks and controls, as the table in `docs/key-concepts.md` says, where it said risks or controls.
* **Rewrite**: Why linked AI governance follows `docs/architecture.md` as it now reads: the missing catalogue, the four doors with the stakeholders the page names, and the couplet. Claims the page does not make were dropped, and `docs/working-with-the-data.md` is cited for the BYOD paragraph.
* **Changed**: What AI-LinkMO adds says curate mode adds, edits and deletes records and that the lookups follow the packaged relationships through the library, as `docs/for-the-curious.md` says. It now cites its sources, among them `docs/cli-examples.md` for the CLI examples run as tests.
* **Changed**: Install and run cites `docs/install.md` as its resource, where the README's install steps moved in #62, and lists every page its steps come from. The steps still match those pages.
* **Changed**: Bring your own data says curate mode adds, edits and deletes records, as `docs/working-with-the-data.md` says.
* **Changed**: AI-LinkMO CLI no longer says it is built from the OpenAPI specification, which #57 replaced with `lib/api/api.yaml` and the schema, and says the tests run most of the listed commands, as `docs/cli-examples.md` says.
* **Changed**: FastAPI Backend's documentation link names `lib/api/README.md`, since `lib/api/openapi.yaml` was deleted in #57, and its description no longer says the endpoints come from an OpenAPI specification.
* **Changed**: the source map places the §What it looks like examples on the architecture page, where #62 moved them from the README.

## 2026-10-14

* **Changed**: the source map's exclusions name `.assets/`, where the screenshots and logos moved from `byo/images/`.
* **Migration**: `base_iri` moved from `https://github.com/noelmcloughlin/ai-linkmo/knowledge/`, a path space GitHub owns, to `https://noelmcloughlin.github.io/ai-linkmo/knowledge/`, where the knowledge-website workflow now publishes each concept, so every concept `id` resolves to its page. The publisher `id`, every concept `id` and every typed-relation target moved with it; `resource` and `distribution` links are unchanged.
* **Prose**: reworded 10 concept bodies in plain English. No fact, link, number or frontmatter changed.
* **Removal**: DuckDB record store, recreated in the same run without a key a Dataset does not take.
* **Added**: DuckDB record store, from `https://github.com/noelmcloughlin/ai-linkmo/tree/main/lib/store`.
* **Changed**: DuckDB record store cites `docs/working-with-the-data.md` under `sources`, since a Dataset takes no `documentation` key.
* **Changed**: AI-LinkMO CLI rewritten for the CLI generated from `lib/api/api.yaml` and the schema since #57; it said the CLI read `lib/api/openapi.yaml`, which is gone.
* **Changed**: FastAPI Backend rewritten for the kernel that registers endpoints from `lib/api/api.yaml` and the schema since #57; `server_dynamic.py` and `openapi.yaml` are gone, and the listings can read the DuckDB store.
* **Changed**: Svelte Web UI says the entity list and the record form are generated, from `lib/api/api.yaml` and the JSON Schema, as `lib/frontend/README.md` says since #57.
* **Changed**: Neo4j Graph Database says the Cypher is fetched from ai-atlas-nexus with `just fetch-cypher`, not generated here, and that `--byod` is refused, as `docs/neo4j.md` says since #57.
* **Changed**: Knowledge-graph export says the Cypher distribution is ai-atlas-nexus's own, fetched at the installed version's tag, since #57 removed `graph/cypher/export.py`.
* **Changed**: Install and run now derives from `docs/install.md`, where #62 moved the README's install steps; the graph step fetches the Cypher, and a step for the store, search and Datasette is added.
* **Changed**: Bring your own data says the Cypher export refuses `--byod` and that the store and browse UI load your files, as `docs/working-with-the-data.md` says since #57.
* **Changed**: Why linked AI governance now cites `docs/architecture.md`, where #62 moved the README's two sections; the argument is unchanged.
* **Changed**: BYOD names `lib/api/api.yaml` for the `byod` parameter, since `openapi.yaml` was removed in #57.
* **Added**: DuckDB record store, from `lib/store/`, the justfile and `docs/working-with-the-data.md`; #57 added it and no concept covered it.
* **Added**: Datasette browse UI, from `lib/browse/`, the justfile and `docs/working-with-the-data.md`; #57 added it and no concept covered it.
* **Changed**: the source map follows #57 and #62: the API and CLI rows name `lib/api/api.yaml` and `exposure.py`, the graph row the fetched Cypher, the install and rationale rows `docs/install.md` and `docs/architecture.md`; rows added for the store and the browse UI, and `website/` and `docs/elements` left out on purpose.

## 2026-09-25

* **Glossary follows the README split**: the six terms now cite `docs/key-concepts.md`, where the table moved, and `glossary/incident` and `glossary/evaluation` are new drafts for the two rows the table gained, each checked against its endpoint and an example id in the packaged data.
* **Cypher export scope corrected**: `datasets/knowledge-graph-export`, `services/graph-db` and `playbooks/bring-your-own-data` said BYOD files reach every door; the Cypher export runs `graph/cypher/export.py`, which loads packaged data only, so only the YAML export includes them.
* **Install and BYOD playbooks re-walked**: `install-and-run` follows the new README, install notes and Neo4j page (`uv sync --extra test`, `npm ci`, `--isDefinedByTaxonomy` in place of a `--taxonomy` flag that does not exist, the CI test command), and the BYOD validation path gains its missing `schema/` segment.
* **SR 11-7 superseded**: SR 26-2 replaced it on 2026-04-17 and its URL now returns 404, so `references/sr-11-7` says so, cites SR 26-2, and is a draft with an open question for the curator.
* **New explanation**: `explanations/what-ai-linkmo-adds` records what the repository adds over AI Atlas Nexus and the provenance its records lack, from the README and `docs/for-the-curious.md`.
* **Source map updated**: `playbooks/knowledge-sources` names the `docs/` pages the README now delegates to, and re-decides the exclusions; 35 concepts re-confirmed against their sources, while FFIEC, ISO and OWASP ML keep their older check because their sites refused or broke the fetch.

## 2026-09-23

* **The docent records a reader's gap without reading the file it goes in.**
  The sidecar now carries `knowledge-feedback.sh`, so ktl-docent hands over
  its own entry and never opens `.lokf/feedback.md`, where other readers' free
  text would enter its session (Snyk W011).

* **The scheduled librarian installs its skill from a tag that has it.** The
  pin read `v0.19.7`, where the skills are named `lokf-*`, so the install step
  (not gated on `KNOWLEDGE_LIBRARIAN_ENABLED`) failed on every run. It moves to
  `v0.23.0`. The scripts under `.lokf/scripts/` and `knowledge-registrar.yaml`
  now match that release's templates: the gate runs `lokf validate
  --check-refs`, and every bundle path is read with `core.quotePath` off.

## 2026-09-18

* **Sidecar brought up to the skills templates**: the wrapper here predated
  the `EXIT`-trap restore and the registrar gate still read confirmations by
  their `by:` line. Synced all five scripts - the conventions pair is new to
  this repository - added `.gitattributes`, and bumped `LOKF_SKILLS_REF`
  from `v0.9.0` to `v0.19.2`. The release workflow now checks release notes
  and the pull request title on a releasing pull request.

## 2026-09-12

* **Toolkit upgrade 0.6.0 -> 0.7.0** (minor - PyPI shows no breaking-change notice; the bundle
  validated unchanged both before and after): bumped the `lokf` floor in `pyproject.toml` to
  `lokf[build]>=0.7.0` and ran `uv sync`.
* **Steady-state refresh - no drift.** Drift surface since the 2026-08-28 run is empty: `git diff`
  between that run's commit (`36354c4`) and current HEAD (`350d533`) touches no file outside
  `.lokf/`, `.claude/skills/`, `.agents/`. Spot-verified against the live tree: `byo/data/` still 9
  files with unchanged AUTOGENERATED headers/bodies (the `eu_ai_act.yaml`/`ffiec_it_handbook.yaml`
  header-vs-body class-name mismatch noted 2026-08-28 is still present, still a repo bug outside
  this bundle's write scope); `graph/*.csv` still 3 crosswalk files; `openapi.yaml` still 28 paths;
  `lib/cli`, `lib/api`, `lib/frontend` (Svelte 5.55 + Vite 8, port-5173 proxy) unchanged; README
  §Key concepts table still backs all six `glossary/` terms; `org/finos` and `org/ibm` resources
  unchanged. All 39 concepts re-confirmed against their `resource`/`derivedFrom`/`source` and given
  a fresh `verified: [{by: process:ktl-librarian, at: 2026-09-12T00:00:00Z}]` event (none of them
  had ever recorded one before this run). No concept content changed, none deleted, no `human:`
  text touched.
* **Source map updated.** Two new repo-root artifacts from an unrelated skill-tooling change (the
  `.claude/skills/*` -> `.agents/skills/*` move, still uncommitted) needed a call: `.agents/` (skill
  definitions - same exclusion as `.claude/`) and `skills-lock.json` (skill-install lockfile). Both
  added to `playbooks/knowledge-sources.md`'s conscious-exclusion list - they are tooling, not
  project knowledge.
* **Still pending from 2026-08-05**: the `base_iri` migration finding (`github.com/...` -> a
  namespace the project controls, proposed `https://w3id.org/ai-linkmo/knowledge/`) remains
  unresolved, awaiting human sign-off.

## 2026-08-28

* **Toolkit upgrade 0.4.0 -> 0.6.0** (0.6.0 realizes the LOKF v0.2 format; no breaking schema changes
  surfaced - the bundle validated unchanged before any edits): bumped the `pyproject.toml` dependency
  to `lokf[build]>=0.6.0` (the `[build]` extra now supplies `linkml`, so the independent `linkml`
  pin was dropped per the step-5 rule) and lowered `requires-python` to `>=3.10` to match the
  toolkit's own floor. Declared the bundle's target format accordingly: root `index.md`
  `lokf_version`/`okf_version` `"0.1"` -> `"0.2"`.
* **Steady-state refresh** (drift surface since the 2026-08-12 run is exactly commit `36354c4`,
  "updated files for latest ai-atlas-nexus schema"): two dataset concepts had drifted and were
  corrected, both now carrying v0.2 `generated` provenance (`by: process:ktl-librarian`) in place
  of the superseded `timestamp`:
  1. `datasets/eu-ai-act` - the encoding's taxonomy row is now `type: RiskTaxonomy` (was
     `Taxonomy`); Format line updated.
  2. `datasets/ffiec-it-handbook` - the taxonomy row is now `type: RiskControlGroupTaxonomy`, and
     each of the 11 booklet groups is now `type: RiskControlGroup` wired to the taxonomy via
     `isDefinedByTaxonomy`; Format line updated.
  `datasets/finos-aigf` was re-verified against the same commit (its `hasStakeholder` slot went
  single- to multivalued) - the concept records the file at knowledge_graph-YAML level, so no
  recorded fact drifted and it is untouched. All other sources: unchanged in git since the last
  run; `byo/data` still 9 files with AUTOGENERATED headers and matching `url:` fields,
  `openapi.yaml` still 28 paths (`/taxonomy`, `/risk`, `/crosswalk` endpoints confirmed). No new
  concepts, no orphans, source map unchanged (the knowledge geography is the same).
  **Repo bug found, outside the bundle's write scope**: the AUTOGENERATED 3-line headers of
  `byo/data/eu_ai_act.yaml` and `byo/data/ffiec_it_handbook.yaml` still name the old classes
  (`Taxonomy`) while their bodies carry the new ones - the concepts record the body truth; the
  headers need regeneration upstream.
  **Still pending from 2026-08-05**: the `base_iri` migration finding (`github.com/...` -> a
  namespace the project controls, proposed `https://w3id.org/ai-linkmo/knowledge/`) remains
  unresolved, awaiting human sign-off.

## 2026-08-12

* **Toolkit upgrade 0.3.0 -> 0.4.0** (minor, additive - Diátaxis support, a CLI `--version` option,
  and an Apache-2.0 licence change; no breaking schema changes, so no human sign-off needed per the
  librarian's step-5 rule): bumped the `lokf` floor in `pyproject.toml` to `>=0.4.0` and ran `uv sync`.
  The bundle validated unchanged against the new schema before any edits.
* **Diátaxis facet applied** to all 32 existing concepts (`genre`, new in LOKF 0.4.0): 2 how-to
  (`playbooks/install-and-run`, `playbooks/bring-your-own-data` - both terse numbered recipes that
  assume competence, so how-to rather than tutorial), the remaining 30 `reference`. Judgement call
  worth flagging for review: `playbooks/knowledge-sources` is typed `Playbook` but tagged
  `genre: reference`, because its body is a per-source lookup table rather than an ordered procedure -
  type and genre are orthogonal by design, so this is legal, but a reviewer may prefer `how-to`.
* **Two gaps promoted from the conscious-exclusion list**, both re-opened by 0.4.0 making
  understanding-oriented prose a first-class type. The 2026-08-10 run excluded README §The Problem,
  §What AI-LinkMO Does and its glossary subsection as "restating facts already captured in
  `services/*` and `references/*`"; that reasoning held for *mechanics* but not for *rationale* or
  *vocabulary*:
  1. Six `glossary/` GlossaryTerms from README §Key concepts, in plain English (Taxonomy, Risk,
     Control / Action, Obligation, Crosswalk, BYOD), each `definedBy` the AI Risk Ontology and each
     verified code-backed (`/taxonomy`, `/risk`, `/control`, `/action`, `/obligation`, `/crosswalk`
     endpoints and the `byod` parameter in `openapi.yaml`). Control and Action are kept as one term
     because the README defines them jointly - splitting them would have meant inventing two
     definitions the source does not give.
  2. `explanations/why-linked-ai-governance` (`type: Explanation`, `genre: explanation`) capturing the
     README's opening argument - framework fragmentation, manual mapping, the governance/engineering
     language gap, and why one shared ontology is what makes the traceability auditable.
  Bundle grew 32 -> 39 concepts. Updated `playbooks/knowledge-sources.md` with two new source rows and
  rewrote the exclusion paragraph to record what was promoted and what stays out (§About Trustworthy
  AI, "What that looks like in practice", §Roadmap - all unchanged).
* **Steady-state refresh** (same run, no drift found): re-verified all 32 pre-existing concepts against
  recorded provenance - `byo/data/*.yaml` still 9 files with matching AUTOGENERATED headers and `url:`
  fields, `graph/` and `graph/cypher/` unchanged, `openapi.yaml` still 28 paths, all four services still
  match current code, README section structure still matches the source map. No concepts deleted.
* **Validation**: `just lokf-validate` -> `OK — 39 concepts in knowledge validate against
  KnowledgeBundle`. `lokf convert --format ttl`: 424 triples, 39 subjects, all inside the knowledge
  namespace, zero dangling internal relation targets; genre distribution 36 reference / 2 how-to /
  1 explanation. All relative markdown links in the bundle resolve.
  **Still pending from 2026-08-05**: the `base_iri` migration finding (`github.com/...` -> a namespace
  the project controls) remains unresolved, awaiting human sign-off. The seven new concepts were minted
  under the existing base for consistency and will need rewriting along with the rest when it moves.

## 2026-08-10

* **Steady-state refresh** (triggered by a README rewrite in the same session): re-verified all 32
  concepts against recorded provenance - `byo/data/*.yaml` still 9 files, `graph/` and `graph/cypher/`
  contents unchanged, all four service concepts (`cli`, `fastapi-backend`, `web-ui`, `graph-db`) still
  match current code and commands. The README rewrite added business-framing narrative (§The Problem,
  §What AI-LinkMO Does incl. a plain-English glossary, §About Trustworthy AI reframed) and a new
  §Roadmap section naming [asago-policy-mapper](https://github.com/asago-ai/asago-policy-mapper) as a
  possible future upstream integration, and reorganized existing content under new headers (§Quick
  Start, §Working With the Data) without changing any facts - also fixed a `./ai graph cyper` ->
  `./ai graph cypher` typo, which already matched `services/graph-db`'s recorded command, so no concept
  drift. Updated `playbooks/knowledge-sources.md`: retitled the install/BYOD source-map rows to the new
  section names, and added the new narrative sections plus §Roadmap to the conscious-exclusion list -
  Roadmap's asago-policy-mapper mention is not code-backed in this repo (no dependency, no integration
  point), so no `references/`/`services/` concept was minted; promote it once a real integration lands.
  No new concepts, no orphans found. `lokf validate` (run via `.venv/bin/lokf` with `.venv/bin` on PATH,
  since neither `uv` nor `just` are on PATH in this environment): `OK — 32 concepts in knowledge validate
  against KnowledgeBundle`. Toolkit version-floor check (step 5): completed later the same
  day via the PyPI JSON API (`uv` is unavailable in this environment) - latest release is 0.3.0, equal
  to the `>=0.3.0` floor in `pyproject.toml`, so no bump needed.
* **Audit** (same day, second run): full section-2 audit on top of the refresh - projected the bundle
  to RDF (`lokf convert --format ttl`): 32 subjects, all internal typed-relation targets resolve (zero
  dangling), no subjects minted outside the knowledge namespace. Verified all nine `byo/data/*.yaml`
  AUTOGENERATED headers and `url:` fields against the datasets' recorded formats and the references'
  `resource` URLs (all match, incl. dual-URL cases nist-sp-800-53-r5 and finos w3id), crosswalk CSV
  header row matches the `fields` list, `openapi.yaml` still 28 paths, orphan sweep of the repo tree
  found nothing unaccounted for. No knowledge changes from the audit itself.
  **Still pending from 2026-08-05**: the `base_iri` migration finding (`github.com/...` -> a namespace
  the project controls) remains unresolved, awaiting human sign-off.

## 2026-08-05

* **Steady-state refresh**: re-verified all 31 concepts against their recorded provenance (all 9
  `byo/data/*.yaml` files present, all graph files present, `openapi.yaml` unchanged at 28 paths, all 4
  services stable). Swept for orphans: no new concepts warranted. Fixed one bug from the audit: the
  bundle-root `index.md` declared `publisher.id =
  .../org/noel-mcloughlin` with no backing concept and the wrong `type: Organization`. Created
  `org/noel-mcloughlin.md` (`type: Person`, `resource: https://github.com/noelmcloughlin`,
  `timestamp: 2026-08-05T00:00:00Z`); corrected publisher type to `Person`; updated `org/index.md` and
  the root TOC. Bundle now has 32 concepts; `lokf validate` passes.
  **Finding for review**: `base_iri: https://github.com/noelmcloughlin/ai-linkmo/knowledge/` violates
  Rule 2 — GitHub owns that path space, so these identifiers can never be made to resolve. Proposed
  migration target: `https://w3id.org/ai-linkmo/knowledge/` (requires a w3id.org redirect PR). Migration
  touches every concept `id`, publisher `id`, and typed-relation target — needs human sign-off before
  proceeding.
* **Schema migration (lokf toolkit upgrade)**: upgraded the lokf toolkit, which ships `lokf validate` (was
  previously unavailable). Running `lokf validate knowledge` against the upgraded schema (now backed by
  `linkml-validate`) revealed three breaking changes from the old `convert`-only validation:
  1. `timestamp` — changed from date-only (`YYYY-MM-DD`) to ISO 8601 datetime with timezone
     (`YYYY-MM-DDTHH:MM:SSZ`). Fixed across all 31 concepts.
  2. `distribution` — changed from a plain list of URL strings to a list of `Distribution` objects
     (`access_url`, `name`, `media_type`). Fixed in `datasets/knowledge-graph-export` and
     `datasets/nist-ai-rmf-crosswalks`.
  3. `fields` — changed from a plain list of strings to a list of `Field` objects (`name`). Fixed in
     `datasets/nist-ai-rmf-crosswalks`.
  Result: `OK — 31 concepts in knowledge validate against KnowledgeBundle.`

## 2026-07-27

* **Steady-state refresh**: re-verified all 31 concepts against their recorded
  provenance (source-map paths, CLI/API OpenAPI wiring, frontend Svelte 5 +
  proxy config, graph export tooling, all 9 `byo/data/*.yaml` headers and
  `url:` fields, index completeness) and projected the bundle to RDF
  (278 triples, 31 subjects, no dangling internal relation targets). One
  drift fixed: the sidecar was renamed `lokf/` -> `.lokf/` since the last run,
  so `playbooks/knowledge-sources.md` now names the `.lokf/` sidecar in its
  exclusion list (and makes `lib/frontend/STATUS.md` and the
  `knowledge-*.yaml` automation workflows conscious exclusions); the root
  README's LLM-visitors pointer to the bundle was repaired to `.lokf/`.

## 2026-07-13

* **Steady-state refresh**: re-verified all 31 concepts against their recorded
  `resource`/`derivedFrom` provenance (manifest identity, CLI/API OpenAPI
  wiring, frontend constants, graph CSV headers, all 9 `byo/data/*.yaml`
  headers and `url:` fields, org/reference facts) - no drift found. Swept the
  full README table of contents for orphans: confirmed `/ares` and LLM
  inferencing are real, code-backed endpoints (`handlers.py`, `cli.py`,
  `vite.config.ts`) but already covered generically by the dynamic
  OpenAPI-driven CLI/API service concepts, so no new concept was minted.
  Extended `playbooks/knowledge-sources.md` with the consciously-excluded
  README sections (§LLM Inferencing, §ARES Evaluation, §ADOPT?, §Curate your
  own Open Data, §Building Python Applications, §Research) so future refreshes
  don't need to re-investigate them.

* **Bootstrap discovery** (ktl-librarian): swept the repository and replaced the
  scaffold's placeholder services with 31 real concepts - 4 services (CLI,
  FastAPI backend, Svelte web UI, Neo4j graph DB), 11 datasets (knowledge-graph
  export, NIST AI RMF crosswalks, and the nine `byo/data/*.yaml` framework
  encodings), 11 references (the external authorities those datasets encode),
  3 playbooks (knowledge-sources map, install-and-run, BYOD), and 2
  organizations (FINOS, IBM). Recorded the scrape map as
  `playbooks/knowledge-sources.md`; rebuilt all section indexes and the root TOC.

* **Initialization**: Scaffolded the LOKF bundle for AI-LinkMO with placeholder
  services. Real concepts to follow.
* **Validation skipped**: `lokf validate` is not yet available in the toolkit
  (PyPI 0.2.0 and git main both lack the command). As a substitute,
  `lokf convert --format ttl knowledge` ran clean. Re-run validation once a
  toolkit release ships `validate` (the CI gate in
  `.github/workflows/knowledge-validate.yaml` will catch it).
