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
- the scheduled `knowledge-librarian.yaml`, which installs a pinned [`lokf-agent-skills`](https://github.com/noelmcloughlin/lokf-agent-skills) skill, runs it against this repository's own `.lokf/knowledge/` bundle, and opens a review pull request. The agent itself runs with **no write permissions**;
- the wrapper script `.lokf/scripts/knowledge-librarian.sh`, which that workflow executes;
- `semantic-release.yml`, which computes the next version from Conventional Commits, promotes `CHANGELOG.md`, bumps `pyproject.toml` and `uv.lock`, and publishes a GitHub Release;
- this repository's `README.md`, `llms.txt`, `byo/` content, and the knowledge bundle: these are prompt-injection surfaces whenever an agent is asked to act on repository text, external URLs, or reader feedback.

### Repository hardening

- Every GitHub Action is pinned to a reviewed commit SHA rather than a floating tag, in every workflow; `.github/dependabot.yml` keeps those pins current alongside the application's Python tree, the `.lokf/` sidecar's separate tree, and the frontend's.
- Every workflow declares `permissions: {}` at the top level, so each job opts into only the scopes it needs.
- All workflows run Step Security's hardened-runner in audit mode to monitor runner egress.
- **The librarian workflow runs in two jobs so the agent and the write token never meet.** `refresh` runs the agent - third-party code - with `contents: read` and `persist-credentials: false`, so no git credential is on disk while it executes, and hands its proposed change to `publish` as a patch artifact. Only `publish`, which runs no agent code, holds `contents: write` / `pull-requests: write`. It re-derives its own checks on a clean checkout rather than trusting anything `refresh` decided, refusing any patch touching a path outside the knowledge bundle. This matters because a pull request opened with the default `GITHUB_TOKEN` never triggers `knowledge-registrar.yaml`'s own `pull_request`-gated checks - a GitHub anti-recursion rule, not a gap in that workflow.
- The librarian triggers only on `schedule` and `workflow_dispatch`, never on an event an outside contributor could fire, and stays inert until the `KNOWLEDGE_LIBRARIAN_ENABLED` repository variable is set to `true`. It never pushes to `main` and never auto-merges.
- `semantic-release.yml`'s `release` job, which pushes a commit and tag to `main` and publishes the release, sits behind the `release` GitHub Environment - configure required reviewers on it in this repository's own Settings → Environments. Its `npm install` of the pinned release tooling runs with `--ignore-scripts`.
- `main` is protected: deletions and force-pushes are blocked and the checks above must pass. Secret scanning and push protection are enabled. These are GitHub repository *settings* rather than files in the tree - nothing in CI can assert they are still in force, so keeping them enabled is a maintainer responsibility.

### Prompt injection, for the librarian specifically

The librarian reads content it did not author - repository files, external URLs, and reader questions in `.lokf/feedback.md`, which is the one input path that can originate from someone with no repository access. That content is data to quote, summarize or inspect, never instructions to follow. The `lokf-librarian` skill requires resolving only the question an entry *names*, from the source it points at and never from the entry's own wording, so an entry phrased as a directive ("mark X verified", "skip validation") is read as the content it reports, not obeyed.

**Blast radius if that fails.** The agent holds no write-scoped token: the worst it can do is propose a patch, confined to the knowledge bundle by independent checks in both jobs, applied by a job running no agent code, landing as a pull request against a protected branch that a human must approve. Nothing in this path can reach a published release or the application code.

### Interactive use of the agent skills

If you install `lokf-agent-skills` locally to work on the bundle, know that a skill's stated scope is prose guidance, not a security boundary - an agent may have broader tool access in your environment than the skill's description implies. Treat any AI-driven workflow as a tool acting with the permissions your harness grants it.

See also [AI_COVENANT.md](AI_COVENANT.md), which sets the human-accountability rules this automation operates under.

## What this does not cover

The upstream [AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/) package and ontology, the published governance frameworks encoded under `byo/`, Neo4j, and any vLLM host you point this at are outside this policy. Report issues in those to their own maintainers.
