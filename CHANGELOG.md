# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Nothing has been released yet. The `v0.1.0` tag is a baseline, not a release: it marks where versioning starts so the first real release is `0.2.0` rather than `1.0.0`. AI-LinkMO is a demo and stays below 1.0.0 deliberately - a breaking change bumps the minor version here. See [CONTRIBUTING.md](CONTRIBUTING.md#releasing-maintainers).

## [Unreleased]

### Added

- **Semantic release.** The version is computed from Conventional Commits on `main`; this file's `## [Unreleased]` section is promoted into a dated heading and used as the release notes, `pyproject.toml` and `uv.lock` are bumped to match, and a GitHub Release is published from it - behind the `release` Environment, so a person approves each one.
- `SECURITY.md`: the reporting route, and what the unauthenticated write endpoints do and do not promise.
