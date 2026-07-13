---
name: okf-librarian
description: 'Scrape the host repository this skill sits inside and build/maintain the `okf/` knowledge bundle as a sidecar, compliant with the Open Knowledge Format (OKF) v0.1 spec. Use when: bootstrapping/creating the okf/ directory (plain files, no tooling - this skill owns its own bootstrap, no scaffolding skill involved); creating or updating concept files under okf/knowledge/; capturing a service (API, CLI, UI, database), dataset, reference framework, playbook, glossary term, or organization as an OKF concept; writing or fixing YAML frontmatter (type/title/description/resource/tags/timestamp); maintaining index.md and log.md; auditing okf/ for correctness, gaps, or bugs; checking OKF conformance; or preparing an OKF knowledge change for human maintainer review.'
---

# OKF Librarian

Maintain `okf/` - the host repository's knowledge captured as an [**Open Knowledge Format (OKF) v0.1**](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle: a directory of Markdown files with YAML frontmatter, no SDK and no build step. This skill covers the librarian lifecycle: **scrape -> build/maintain -> audit -> hand off for review.**

> Scope: this skill owns **only** `okf/`. A semantic sibling `lokf/` would be
> owned by the separate **lokf-librarian** skill; where the repo maintains both,
> keep the two bundles consistent but edit each through its own skill. The
> scheduled automation described in lokf-librarian §4 covers `lokf/` only -
> refresh `okf/` by running this skill on demand.

## Layout

```
okf/
|--- knowledge/         # the OKF bundle
    |--- index.md       # root listing; carries only okf_version frontmatter
    |--- log.md         # change history (reserved name)
    |--- services/  datasets/  references/
    |--- playbooks/  glossary/  org/
    |--- ...              # one Markdown file per concept
```

> **Bootstrap (this skill owns it):** if `okf/` is missing, create
> `okf/knowledge/` with a root `index.md` (frontmatter `okf_version: "0.1"`
> only), an empty `log.md`, and the domain directories as concepts are added.
> Plain OKF is just files - no tooling, so unlike `lokf/` there is no separate
> scaffolding skill and none is needed; bootstrap is simply the first act of
> this skill's Scrape & build step.

## Golden Rules (OKF v0.1)

1. **One concept per file; the path is the identity.** `services/api.md`
   is concept `services/api`. Organize directories by domain, not by the
   spec.
2. **`type` is the only required frontmatter field.** It must be present and
   non-empty on every non-reserved `.md` file - this is the one hard conformance
   rule. Use descriptive, self-explanatory values
   (`Service`, `Metric`, `Policy`, `Playbook`, `GlossaryTerm`, `Reference`, ...).
3. **Recommended fields, in priority order:** `title`, `description` (one
   sentence - it feeds index/search snippets), `resource` (canonical URI of the
   underlying asset; omit for abstract concepts), `tags` (YAML list), `timestamp`
   (ISO 8601). Producers MAY add any other keys.
4. **`index.md` and `log.md` are reserved** at every level. Never use them as
   concept documents. `index.md` carries **no** frontmatter except the bundle root
   (`okf_version: "0.1"` only).
5. **Cross-link with ordinary Markdown links; the prose carries the meaning.**
   Prefer **bundle-relative** links beginning with `/` (`/glossary/risk.md`) -
   stable when files move. Relative links (`./other.md`) are allowed. The link is
   an untyped directed edge; broken links are tolerated (they may be
   not-yet-written knowledge), so do not delete a concept just to fix a dangling
   link.
6. **Favor structural Markdown** - headings, lists, tables, fenced code - over
   free prose. Conventional headings when applicable: `# Schema`, `# Examples`,
   and `# Citations` - the last lists the external sources backing body claims,
   numbered.
7. **Consume permissively.** Never make a concept invalid because of missing
   optional fields, unknown `type` values, unknown extra keys, or broken links.

## 1. Scrape & build

Derive concepts from the host repository (or, as an edge case, any directory tree) - do not invent facts. **The bundle itself is the scrape map**: every concept's `resource` records the asset it describes, and the map of knowledge sources is itself a reviewed concept. Later runs re-verify recorded sources rather than re-discovering the repo from scratch.

### Bootstrap discovery - first run, or whenever the bundle has no real concepts

Sweep the repository with generic heuristics and map what you find to types:

- **Services** - APIs, CLIs, UIs, workers, databases. Find them via manifests
  (`package.json`, `pyproject.toml`, `go.mod`, ...), entry points,
  `Dockerfile`/compose files, and CI config. One `Service` concept per access
  pattern; set `resource` to its source tree.
- **Datasets** - data and schema files (CSV/YAML/JSON/SQL), fixtures,
  migrations. Link each to the `Reference` standard it encodes, where one exists.
- **References** - the external standards, specs, and ontologies the code or
  data encodes; cite the canonical URL as `resource`.
- **Playbooks** - root and per-component `README.md`/docs install, run, and
  architecture how-tos.
- **Glossary** - domain terms recurring across code, data, and docs.
- **Org** - owners and publishers named in ownership files (`CODEOWNERS`,
  manifest authors) or inside data files, linked from the concepts they own or
  publish; add one only when another concept needs the link.

Record the resulting map as a concept: **`playbooks/knowledge-sources.md`**
(`type: Playbook`), listing each knowledge source (repo path or external URL),
the type(s) it yields, and how to re-check it. Discovery output thereby lives in
the bundle, versioned and human-reviewed like every other concept - not in this
skill.

### Steady-state refresh - every later run

1. **Re-verify `resource`.** For each concept, follow its `resource` back to the
   asset: does it still exist, are the body's claims still true? Fix drift.
2. **Re-walk `playbooks/knowledge-sources.md`.** Listed sources may have grown
   new assets since the last run.
3. **Sweep for orphans.** Files or directories no concept and no source-map
   entry accounts for are gap candidates: add a concept, extend the source map,
   or consciously leave them out.
4. **Update the source map** whenever the repository's knowledge geography
   changes.

For each concept: write the frontmatter (Rule 2-3), then a Markdown body that
links to related concepts (Rule 5). Add an entry to the nearest `index.md` and to
`log.md`.

Frontmatter template - a **fictional** "Acme Platform" example; never copy its
values, derive your own from the host repository:

```markdown
---
type: Service
title: Orders API
description: REST API serving order data, generated dynamically from services/orders/openapi.yaml.
resource: https://github.com/acme/platform/tree/main/services/orders
tags: [api, orders]
timestamp: 2026-07-08T00:00:00Z
---

# Overview

The **Orders API** exposes REST endpoints over the order data, consumed by the [CLI](/services/cli.md) and [web UI](/services/frontend.md)...
```

### index.md and log.md

- `index.md` groups concepts under headings, one bullet per concept, each with the
  concept's `description`:
  ```markdown
  # Services

  * [Orders API](services/orders-api.md) - REST API serving order data.
  ```
- `log.md` is date-grouped, **newest first**, ISO `YYYY-MM-DD` headings. The
  leading bold word is a convention:
  ```markdown
  ## 2026-07-11
  * **Update**: Refreshed [Orders API](/services/orders-api.md) endpoint docs.
  * **Creation**: Added [CLI](/services/cli.md).
  ```

## 2. Audit (correctness, gaps, bugs)

Check conformance first - the two hard OKF rules: every non-reserved `.md` file
opens with a parseable `---` frontmatter block and carries a non-empty `type`.
Then reason about content quality, auditing for:

- **Correctness** - does each concept still match the code/docs it describes?
  Stale `resource` URIs, renamed modules, removed endpoints, changed schemas.
- **Gaps** - new code/data files with no concept; concepts missing `description`,
  `resource`, or `timestamp`; sparse `index.md` sections.
- **Bugs** - malformed YAML, missing/empty `type`, `index.md`/`log.md` misused as
  concepts, non-ISO timestamps, broken *intended* links (distinguish from
  deliberately-forward links), duplicated concept IDs.
- **Consistency with `lokf/`** (when the repo maintains a semantic `lokf/`
  sibling) - the same real-world concepts should exist in both bundles; flag
  drift for the lokf-librarian skill to reconcile.

Report findings as a checklist and fix the mechanical ones directly.

## 3. Hand off for human maintainer review

Knowledge changes are proposed, not self-published. Open a PR scoped to `okf/`
with:

- A summary of what was scraped/changed and the source of truth for each claim.
- The conformance-check result (frontmatter + non-empty `type` on every concept).
- Explicit callouts where authority lives outside the repository - the
  standards, ontologies, and upstream systems the bundle's `Reference` concepts
  point at - so a maintainer can verify against the canonical source. Never
  assert facts from those systems without a citation a reviewer can follow
  (`# Citations`).

A human maintainer approves before merge. Treat their review as the trust
boundary.
