# Security Policy

## This repository

AI-LinkMO is a **demo**: a CLI, a FastAPI backend, a Svelte web UI, and a set of governance frameworks encoded for the AI Risk Ontology. Unlike the sibling LOKF repositories, it ships real runtime code, so it has two distinct risk surfaces - the application you run locally, and this GitHub repository's own automation. Both are covered below.

Nothing here is built to be exposed to a network. [Running it](#running-it-safely) says what that means in practice, and [Known limitations](#known-limitations-accepted-for-now) lists what is deliberately not hardened yet, so you are not surprised by it.

## Reporting a vulnerability

Please use GitHub's [private vulnerability reporting](https://github.com/noelmcloughlin/ai-linkmo/security/advisories/new) rather than a public issue. Include:

- the affected component (a route under `lib/api/`, the CLI, the frontend, a workflow under `.github/workflows/`, or the librarian wrapper script);
- how it is exploitable, and whether it needs local access or only a reachable port;
- any proof of concept or minimally sufficient reproduction details.

Please report anything that lets a request reach beyond the documented behaviour of a route - path traversal out of `byo/data/`, code execution through an uploaded file, or an unexpected outbound request - even if the endpoint is one of the unauthenticated ones listed below. "It has no auth" is a known limitation; "it writes outside its directory" is a vulnerability.

## Supported versions

**No release has been cut yet**, and this project is pre-1.0 by design - see [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers). There is no supported release line and no backporting: fixes land on `main` and ship in the next release.

## Running it safely

- **Run on localhost.** The API binds for local development and assumes a trusted caller. If you must expose it, put it behind a reverse proxy that authenticates every request - do not rely on anything in this repository to do that for you.
- **Treat `byo/data/` and `graph/` as writable.** The write paths below rewrite files there in place. Run against a checkout you can `git checkout --` back, not a directory holding anything you care about.
- **Framework encodings are interpretations, not authority.** No encoding under `byo/` has been checked by a named person against its framework's published text. Do not make a compliance decision from this data without reading the source; [AI_COVENANT.md](AI_COVENANT.md) says why this matters more here than in most projects.

## Known limitations, accepted for now

These are documented rather than fixed because this is a demo and the affected shapes are expected to change. They are not vulnerabilities - reporting them as such tells us nothing new - but each becomes one the moment this runs anywhere but localhost.

- **The write endpoints are unauthenticated.** `PUT /byo`, and `export=true` on `/graph` and `/crosswalk`, change files under `byo/data/` and `graph/` with no credential. `lib/api/openapi.yaml` declares an `X-API-Key` security scheme on the upload, but **the server does not enforce it** - the spec describes the intended shape, not current behaviour. Enforcing it, and rejecting writes outside the two data directories, is the first hardening step planned.
- **The web UI's login is a persona picker**, not authentication. It selects which role's view to render; it checks nothing and grants nothing.
- **The UI fetches persona avatars from `ui-avatars.com`**, a third-party origin, at render time. Offline or air-gapped use will show broken images, and that origin sees your traffic.
- **No CodeQL or dependency-vulnerability scanning is configured** for the Python and JavaScript trees. Dependabot keeps versions current (`.github/dependabot.yml`), which is not the same thing. Worth adding once the API's shape settles.
- **`graph/` holds committed generated output** (~4 MB). It is regenerable, and the export commands rewrite it in place; treat it as a build artifact that happens to be tracked, not as reviewed content.

## This repository's own automation

### Scope

The execution surfaces outside the application itself are:

- `lint-and-docs.yaml` (ShellCheck, `actionlint`, markdownlint, link-checking, codespell), `cli-tests.yml`, `ui-tests.yml`, and `knowledge-registrar.yaml`, which validates the knowledge bundle's *form* on every `.lokf/**` pull request - all read-only;
- the scheduled `knowledge-librarian.yaml`, which installs a pinned [`knowledge-trust-ladder`](https://github.com/noelmcloughlin/knowledge-trust-ladder) skill, runs it against this repository's own `.lokf/knowledge/` bundle, and opens a review pull request. The agent itself runs with **no write permissions**;
- the wrapper script `.lokf/scripts/knowledge-librarian.sh`, which that workflow executes;
- `semantic-release.yml`, which computes the next version from Conventional Commits, promotes `CHANGELOG.md`, bumps `pyproject.toml` and `uv.lock`, and publishes a GitHub Release;
- this repository's `README.md`, `llms.txt`, `byo/` content, and the knowledge bundle: these are prompt-injection surfaces whenever an agent is asked to act on repository text, external URLs, or reader feedback.

### Repository hardening

- Every GitHub Action is pinned to a reviewed commit SHA rather than a floating tag, in every workflow; `.github/dependabot.yml` keeps those pins current alongside the application's Python tree, the `.lokf/` sidecar's separate tree, and the frontend's.
- Every workflow declares `permissions: {}` at the top level, so each job opts into only the scopes it needs.
- All workflows run Step Security's hardened-runner in audit mode to monitor runner egress.
- **The librarian workflow runs in two jobs so the agent and the write token never meet.** `refresh` runs the agent - third-party code - with `contents: read` and `persist-credentials: false`, so no git credential is on disk while it executes, and hands its proposed change to `publish` as a patch artifact. Only `publish`, which runs no agent code, holds `contents: write` / `pull-requests: write`. What each of those jobs checks, and why, is the template's design - see the next section.
- `semantic-release.yml`'s `release` job, which pushes a commit and tag to `main` and publishes the release, sits behind the `release` GitHub Environment - configure required reviewers on it in this repository's own Settings → Environments. Its `npm install` of the pinned release tooling runs with `--ignore-scripts`.
- **`main` is protected, but not by a merge gate.** Deletions and force-pushes are blocked and linear history is required. A rule requiring pull requests, or requiring status checks to pass, is deliberately **not** enabled: rulesets apply both to direct pushes as well as to merges, and the release workflow's own commit to `main` cannot be exempted from them - a bypass list accepts roles, teams, GitHub Apps and Dependabot, and `github-actions[bot]` is none of those. What gates a change here is access control, not a rule: only the maintainer can write to this repository, CI runs on every pull request, and its result is read before merging. Secret scanning and push protection are enabled. These are GitHub repository *settings* rather than files in the tree - nothing in CI can assert they are still in force, so keeping them enabled is a maintainer responsibility.

### The librarian workflow: what is inherited, what this repository owns

`.github/workflows/knowledge-librarian.yaml` and `.lokf/scripts/knowledge-librarian.sh` are copies of the `ktl-sidecar` template in [`knowledge-trust-ladder`](https://github.com/noelmcloughlin/knowledge-trust-ladder), and their security design is that repository's, documented once there:

- how the two-job split keeps the agent away from any write-scoped token, and why the `publish` job's own checks - path confinement derived from the patch itself, refusal of any added `by: human:` claim - are the backstop rather than the wrapper's: [Prompt-injection guards](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/threat-model.md#prompt-injection-guards);
- how the `ktl-librarian` skill treats `.lokf/feedback.md`, and everything else it did not author, as content to inspect and never as instructions to follow: the same section;
- why a skill's stated scope is prose, not a permission, when you run it interactively: [Interactive use: scope is advisory, not enforced](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/threat-model.md#interactive-use-scope-is-advisory-not-enforced);
- why the review PR it opens does not trigger this repository's `pull_request` checks, and what stands in for them: [Repository hardening](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/threat-model.md#repository-hardening).

Restating that design here would imply this repository controls it. It does not: a change there reaches here on the next `TRUST_LADDER_SKILLS_REF` bump, and a copy here would go stale with nothing in CI to notice. What this repository does own, and is accountable for:

- **The deployed copy.** Both files carry every job and check the template does; the only edits are `persist-credentials: false` on the read-only checkout steps (stricter than the template, not looser) and `uv sync --locked`, matching this repository's own lockfile discipline elsewhere. Anything further that is edited locally becomes this repository's responsibility rather than the template's; `diff` against `skills/ktl-sidecar/templates/` in a checkout of `knowledge-trust-ladder` to confirm.
- **The switches.** The agent step runs only while the `KNOWLEDGE_LIBRARIAN_ENABLED` repository variable is `true`; `AGENT_CLI` chooses *which* non-interactive agent runs, never *what command*; the workflow triggers only on `schedule` and `workflow_dispatch`. All three are readable in this repository's own YAML.
- **The surfaces.** What the librarian reads *here* is `README.md`, `llms.txt`, `byo/` content and the `.lokf/knowledge/` bundle - and `.lokf/feedback.md`, the one input that can originate from someone with no repository access.
- **The consequence if the inherited guards fail.** The agent holds no write-scoped token, so the worst outcome is a proposed patch confined to the knowledge bundle and `.lokf/feedback.md`, applied by a job that runs no agent code, arriving as a pull request that only the maintainer can merge, after reading it. Nothing on that path reaches a published release or the application code.
- **The attribution gate is installed.** `.github/workflows/knowledge-registrar.yaml` here carries the template's `validate`, `provenance` and `attestation` jobs, unchanged, so a newly added `human:` confirmation must be backed by evidence GitHub holds - an approving review, or a verified signature on the introducing commit. [Human attribution](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/threat-model.md#human-attribution-human-is-a-claim-not-a-credential) has the design and its stated limits.

See also [AI_COVENANT.md](AI_COVENANT.md), which sets the human-accountability rules this automation operates under.

## What this does not cover

The upstream [AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/) package and ontology, the published governance frameworks encoded under `byo/`, Neo4j, and any vLLM host you point this at are outside this policy. Report issues in those to their own maintainers.
