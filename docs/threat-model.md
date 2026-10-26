# Threat model

AI-LinkMO has two risk surfaces: the application you run locally (a CLI, a FastAPI backend, a Svelte web UI, and governance frameworks encoded for the AI Risk Ontology), and this GitHub repository's automation. [SECURITY.md](../SECURITY.md) is the policy: how to report, and what holds each surface. This page gives the reasoning for what this repository owns. The librarian, sync, release and website workflows are copies of the `ktl-sidecar` templates in [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder), whose design is documented once in [its threat model](https://w3id.org/ktl/docs/threat-model/).

## Running the application

Nothing here is built to be exposed to a network.

- **Run on localhost.** The API binds for local development and assumes a trusted caller. If you must expose it, put it behind a reverse proxy that authenticates every request; nothing in this repository does that for you.
- **Treat `byo/data/` and `graph/` as writable.** The write paths below rewrite files there in place. Run against a checkout you can `git checkout --` back, not a directory holding anything you care about.
- **Framework encodings are interpretations, not authority.** No encoding under `byo/` has been checked by a named person against its framework's published text. Do not make a compliance decision from this data without reading the source; [AI_COVENANT.md](../AI_COVENANT.md) says why this matters more here than in most projects.

## Known limitations, accepted for now

These are documented rather than fixed because this is a demo and the affected shapes are expected to change. They are not vulnerabilities, and reporting them as such tells us nothing new, but each becomes one the moment the application runs anywhere but localhost.

- **The write endpoints are unauthenticated.** `PUT /byo`, and `export=true` on `/graph` and `/crosswalk`, change files under `byo/data/` and `graph/` with no credential. The contract the server publishes at `/openapi.json` declares an `X-API-Key` security scheme on the upload (it comes from the overlay in `lib/api/api.yaml`), but the server does not enforce it: the contract describes the intended shape, not current behaviour. Enforcing it, and rejecting writes outside the two data directories, is the first hardening step planned.
- **The web UI's login is a persona picker**, not authentication. It selects which role's view to render; it checks nothing and grants nothing.
- **The UI fetches persona avatars from `ui-avatars.com`**, a third-party origin, at render time. Offline or air-gapped use shows broken images, and that origin sees your traffic.
- **No CodeQL or dependency-vulnerability scanning is configured** for the Python and JavaScript trees. Dependabot keeps versions current (`.github/dependabot.yml`), which is not the same thing. It is worth adding once the API's shape settles.
- **`graph/` holds committed generated output** (about 2 MB of YAML and CSV). It is regenerable, and the export commands rewrite it in place; treat it as a build artefact that happens to be tracked, not as reviewed content. The Cypher export is fetched from ai-atlas-nexus on request and is not tracked.

## Repository hardening

- Every GitHub Action is pinned to a reviewed commit SHA rather than a floating tag, in every workflow. `.github/dependabot.yml` keeps those pins current, alongside the application's Python tree, the `.lokf/` sidecar's separate tree, and the frontend's.
- Every workflow declares `permissions: {}` at the top level, so each job opts into only the scopes it needs, and runs Step Security's harden-runner in audit mode to monitor runner egress.
- `semantic-release.yml`'s `release` job, which pushes a commit and tag to `main` and publishes the release, runs in the `release` GitHub Environment, which admits only `main`. Required reviewers on that Environment are not configured at present, so a qualifying merge releases with no human step; Settings → Environments is where to add them. Its `npm install` of the pinned release tooling runs with `--ignore-scripts`.
- **`main` is protected, but not by a merge gate.** A ruleset blocks deletion and force-pushes and requires linear history. A rule requiring pull requests or passing status checks is deliberately not enabled: rulesets apply to direct pushes as well as merges, and the release workflow's own commit to `main` cannot be exempted, because a bypass list accepts roles, teams, GitHub Apps and Dependabot, and `github-actions[bot]` is none of those. What gates a change here is access control: only the maintainer can write to this repository, CI runs on every pull request, and its result is read before merging.
- Secret scanning, push protection and Dependabot security updates are enabled.

The ruleset, the Environments and the scanning are repository settings, not files in the tree. Nothing in CI can assert that they are still in force, so keeping them on is the maintainer's responsibility.

## The librarian workflow: what is inherited, what this repository owns

`.github/workflows/knowledge-librarian.yaml` and `.lokf/scripts/knowledge-librarian.sh` are copies of the template, and their security design is the template's:

- how the job split keeps the agent away from any write-scoped token, and why the `publish` job's own checks (path confinement derived from the patch itself, refusal of any change to a person's record) are the backstop rather than the wrapper's: [Prompt-injection guards](https://w3id.org/ktl/docs/threat-model/#prompt-injection-guards);
- how the `ktl-librarian` skill treats `.lokf/feedback.md`, and everything else it did not author, as content to inspect and never as instructions to follow: the same section;
- why a skill's stated scope is prose, not a permission, when you run it interactively: [Interactive use: scope is advisory, not enforced](https://w3id.org/ktl/docs/threat-model/#interactive-use-scope-is-advisory-not-enforced);
- why the review pull request it opens does not trigger this repository's `pull_request` checks, and what stands in for them: [Repository hardening](https://w3id.org/ktl/docs/threat-model/#repository-hardening).

The workflow runs in three jobs. `earlier` runs no agent and holds only `pull-requests: read`: it reads what became of this workflow's earlier pull requests, so a scheduled run opens no second one beside an open one and does not propose again what a person declined. `refresh` runs the agent, which is third-party code, with `contents: read` and `persist-credentials: false`, so no git credential is on disk while it executes. The agent's one output is `.lokf/patch.yaml`, which `knowledge-apply.sh` applies, and `refresh` hands the result to `publish` as a patch artifact. Only `publish`, which runs no agent code, holds `contents: write` and `pull-requests: write`.

Moving the pin (`TRUST_LADDER_SKILLS_REF` and the commit `TRUST_LADDER_SKILLS_SHA` beside it) changes only the skill the scheduled run installs. The workflows and the files under `.lokf/scripts/` and `.lokf/m365/` are copies of `skills/ktl-sidecar/templates/` that `knowledge-sync.yaml` moves with the pin, from the release it names, and `knowledge-preflight.sh` reports drift on its `copies` line where a sidecar is installed to compare against. What this repository does own, and is accountable for:

- **The deployed copy.** Both files carry every job and check the template does. The wrapper is byte-identical to its template, and the workflow differs from its template only in the pin the install step names. Anything further edited locally becomes this repository's responsibility rather than the template's; `diff` against `skills/ktl-sidecar/templates/` in a checkout of knowledge-trust-ladder to confirm.
- **The switches.** The agent step runs only while the `KNOWLEDGE_LIBRARIAN_ENABLED` repository variable is `true`. `AGENT_CLI` chooses *which* non-interactive agent runs, never *what command*, and its credential, the `AGENT_API_KEY` secret or the job token, reaches only the agent. The workflow triggers only on `schedule` and `workflow_dispatch`. All three are readable in this repository's own YAML.
- **The surfaces.** What the librarian reads here is `README.md`, `llms.txt`, `byo/` content and the `.lokf/knowledge/` bundle, and `.lokf/feedback.md`, the one input that can come from someone with no repository access. The same files are prompt-injection surfaces whenever any agent is asked to act on repository text, external URLs or reader feedback.
- **The consequence if the inherited guards fail.** The agent holds no write-scoped token, so the worst outcome is a proposed patch confined to the knowledge bundle, `.lokf/feedback.md` and `.lokf/questions.md`, applied by a job that runs no agent code, arriving as a pull request that only the maintainer can merge, after reading it. Nothing on that path reaches a published release or the application code.
- **The attribution gate.** `.github/workflows/knowledge-registrar.yaml` carries the template's `validate`, `provenance` and `attestation` jobs, unchanged, so a `human:` event that a change adds, alters or removes must be backed by that person's evidence GitHub holds: an approving review, or a verified signature on the commit. [Human attribution](https://w3id.org/ktl/docs/threat-model/#human-attribution-human-is-a-claim-not-a-credential) has the design and its stated limits.
