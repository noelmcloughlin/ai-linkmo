# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Nothing has been released yet. The `v0.1.0` tag is a baseline, not a release: it marks where versioning starts so the first real release is `0.2.0` rather than `1.0.0`. AI-LinkMO is a demo and stays below 1.0.0 deliberately - a breaking change bumps the minor version here. See [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers).

## [Unreleased]

### Changed

- **The skills repository is now `knowledge-trust-ladder`**, formerly `lokf-agent-skills`: a third-party repository named after the format read as upstream LOKF's official home.
- **Every link, both `npx skills add` lines and `LOKF_SKILLS_REPO` follow it.** The skill names are unchanged, and GitHub redirects the old paths.
- **The signing-guide link pointed at a heading that no longer exists**: that repository's `CONTRIBUTING.md#signing-your-commits`. The guide has its own page now, `docs/signing-commits.md`.

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
