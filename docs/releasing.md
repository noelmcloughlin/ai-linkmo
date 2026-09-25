# How this repository releases

No release has been cut yet; `pyproject.toml` says 0.1.0, matching the `v0.1.0` baseline tag. [CHANGELOG.md](../CHANGELOG.md)'s `## [Unreleased]` section is written as changes happen, and [`semantic-release.yml`](../.github/workflows/semantic-release.yml) does the rest on each merge to `main`: it computes the next version from [Conventional Commits](https://www.conventionalcommits.org/), promotes that section into a dated heading, bumps `pyproject.toml` and `uv.lock`, and publishes a GitHub Release from the same text, once a person approves it in the `release` Environment. Only `feat:`, `fix:` and `security:` cut a release. Once `KNOWLEDGE_RELEASE_ENABLED` is set, each release also carries the `.lokf/knowledge/` bundle as a zip, when it changed.

## The version stays below 1.0.0

This is a demo, and the shapes of the API, the web UI and the CLI will change. The `v0.1.0` tag is a baseline, not a release: it stops semantic-release defaulting the first release to 1.0.0, and a breaking change bumps the minor version, not the major one. Reaching 1.0.0 will be a decision, not something a commit message can trigger.

## For maintainers

[CONTRIBUTING.md](../CONTRIBUTING.md#releasing-maintainers) has the steps: what to write in the changelog, how to type a commit or a pull-request title so it releases, and the `release` Environment's reviewers. The shared design behind the pipeline, which this repository has in common with [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder) and the two Obsidian plugins, is [that repository's releasing page](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/releasing.md).
