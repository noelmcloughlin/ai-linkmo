# Security Policy

*This file is a policy, not a threat model. It says how to report, what this repository ships, what executes here, and what holds each surface. Each is a line or two that links to where the reasoning lives: this repository's [threat model](docs/threat-model.md), a workflow header, or the shared [ktl-sidecar threat model](https://w3id.org/ktl/docs/threat-model/). `lint-and-docs.yaml` holds the file to a word budget so it stays that way.*

## Reporting a vulnerability

Use GitHub's [private vulnerability reporting](https://github.com/noelmcloughlin/ai-linkmo/security/advisories/new), not a public issue. Say which component is affected (a route under `lib/api/`, the CLI, the frontend, a workflow under `.github/workflows/`, or the librarian wrapper script), how it is exploitable, whether it needs local access or only a reachable port, and how to reproduce it.

Report anything that lets a request reach beyond a route's documented behaviour, such as path traversal out of `byo/data/`, code execution through an uploaded file, or an unexpected outbound request, even on an unauthenticated endpoint. "It has no auth" is a known limitation; "it writes outside its directory" is a vulnerability.

## Supported versions

This project is pre-1.0 by design ([CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers)). There is no supported release line and no backporting: fixes land on `main` and ship in the next release.

## What this repository ships

AI-LinkMO is a **demo**: a CLI, a FastAPI backend, a Svelte web UI, and governance frameworks encoded for the AI Risk Ontology. Nothing in it is built to be exposed to a network. Run it on localhost, against a checkout you can restore, and read a framework's published text before acting on its encoding; [Running the application](docs/threat-model.md#running-the-application) says why.

These limitations are known and accepted for now. Each becomes a vulnerability once the application runs anywhere but localhost; [the threat model](docs/threat-model.md#known-limitations-accepted-for-now) has the detail and what is planned.

- The write endpoints, `PUT /byo` and `export=true` on `/graph` and `/crosswalk`, are unauthenticated, and the server does not enforce the `X-API-Key` scheme `/openapi.json` declares.
- The web UI's login is a persona picker, not authentication.
- The UI fetches persona avatars from `ui-avatars.com`, a third-party origin.
- No CodeQL or dependency-vulnerability scanning is configured.
- `graph/` holds committed generated output that the export commands rewrite in place.

## What executes here

| Surface | What holds it |
| --- | --- |
| `lint-and-docs.yaml`, `cli-tests.yml`, `ui-tests.yml`, and `knowledge-registrar.yaml` on any `.lokf/**` change: linters, tests and the bundle's form | Read-only jobs. A `human:` event in the bundle must be backed by that person's approving review or verified signature. [Human attribution](https://w3id.org/ktl/docs/threat-model/#human-attribution-human-is-a-claim-not-a-credential). |
| `semantic-release.yml`, which pushes a release commit and tag to `main`, publishes the GitHub Release and dispatches `knowledge-release.yaml` | Runs in the `release` Environment, which admits only `main`, installing its pinned tools with `--ignore-scripts`. Required reviewers are not configured, so a qualifying merge releases with no human step. [Repository hardening](docs/threat-model.md#repository-hardening). |
| `knowledge-librarian.yaml` and `.lokf/scripts/knowledge-librarian.sh`, copies of the `ktl-sidecar` template, running an LLM agent on a schedule | The agent never meets a write token; `publish`, which runs no agent code, confines the patch to the bundle and opens a pull request the maintainer merges. Inert until `KNOWLEDGE_LIBRARIAN_ENABLED` is `true`. [What this repository owns](docs/threat-model.md#the-librarian-workflow-what-is-inherited-what-this-repository-owns). |
| `knowledge-release.yaml`, which attaches the bundle to a release as a zip | Inert until dispatched or armed; only its `attach` job, which runs no third-party packages, can write. |
| `knowledge-sync.yaml` and `.lokf/scripts/knowledge-sync.sh`, which open the weekly pull request that moves the skills pin and the copies | Only `publish` and `push-workflows` hold `KNOWLEDGE_SYNC_TOKEN`, from the `knowledge-sync` Environment; `push-workflows` waits for a `knowledge-sync-review` reviewer, and nothing from the release runs. [The sync workflow](https://w3id.org/ktl/docs/threat-model/#the-sync-workflow). |
| `knowledge-website.yaml`, which builds and deploys the bundle's site | The build runs under a read-only token; only `deploy`, which runs GitHub's deploy-pages action alone, holds the Pages scopes. [The website](https://w3id.org/ktl/docs/threat-model/#the-website). |
| `README.md`, `llms.txt`, `byo/` content, the knowledge bundle and `.lokf/feedback.md`, read by agents | Content, never instructions: each skill quotes what it did not author. [Prompt-injection guards](https://w3id.org/ktl/docs/threat-model/#prompt-injection-guards). |

Every workflow declares `permissions: {}` at the top, pins its actions to commit SHAs that Dependabot keeps current, and runs harden-runner in audit mode. A ruleset on `main` blocks deletion and force-pushes and requires linear history, and secret scanning with push protection is on. Those are repository settings, not files: nothing in CI can assert them, so keeping them on is the maintainer's job.

## Not covered

- The upstream [AI Atlas Nexus](https://ibm.github.io/ai-atlas-nexus/) package and ontology, the published governance frameworks encoded under `byo/`, Neo4j, and any vLLM host you point this at: report issues in those to their own maintainers.
- Whether a framework encoding or a bundle concept is *true*. [AI_COVENANT.md](AI_COVENANT.md) sets the human-accountability rules this automation operates under.
