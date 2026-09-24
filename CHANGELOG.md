# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Nothing has been released yet. The `v0.1.0` tag is a baseline, not a release: it marks where versioning starts so the first real release is `0.2.0` rather than `1.0.0`. AI-LinkMO is a demo and stays below 1.0.0 deliberately - a breaking change bumps the minor version here. See [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers).

## [Unreleased]

### Fixed

- **The scheduled librarian installs its skill from `v0.23.1`.** The pin still named `v0.19.7`, which has no `skills/ktl-librarian`, so the weekly run failed at that step.

### Security

- **The sidecar carries `knowledge-feedback.sh`.** ktl-docent records a reader's gap through it and never opens `feedback.md`, so no other reader's text enters its session (Snyk W011).
- **The sidecar scripts and registrar gate match the `v0.23.1` templates.** A bundle path with a byte above 0x7f is now read rather than skipped, and one git must quote is refused; relation targets are checked by `lokf validate --check-refs`.

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
