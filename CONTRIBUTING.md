# Contributing to AI-LinkMO

*This file is a checklist, not a design log. Each rule is a line or two that links to where its reasoning lives: a code comment, a workflow header, or a linked page. `lint-and-docs.yaml` holds the file to a word budget so it stays that way.*

Thanks for your interest in improving AI-LinkMO!

## What this project is

AI-LinkMO demonstrates four ways into one linked AI-governance knowledge graph: a CLI (`./ai`), an HTTP API, a Svelte web UI, and direct graph queries.

| Path | Lives in |
| --- | --- |
| CLI | `ai`, `ai-risk-ontology-linkmo/` |
| HTTP API | `ai-risk-ontology-linkmo/`, `lib/api/` |
| Web UI | `lib/frontend/` |
| Graph, ontology, crosswalks | `graph/`, `byo/` |
| Tests | `lib/test/` |
| This repo's own knowledge bundle | `.lokf/knowledge/` |

[docs/repository-layout.md](docs/repository-layout.md) has the rest.

## Development setup

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required; Node 22 for the frontend.

```bash
git clone https://github.com/noelmcloughlin/ai-linkmo.git
cd ai-linkmo
uv sync --extra test --extra browse   # application, test and browse dependencies
./ai --help                           # runs the linkmo project's command line via uv
```

For the web UI:

```bash
cd lib/frontend
npm ci
npm run dev
```

### Bringing your own data

`byo/data/` holds the encoded governance frameworks and `byo/notes/EXAMPLES.md` walks through the four access patterns; the `bring-your-own-data` playbook in the knowledge bundle explains the format.

### Agent skills (optional - only for editing this repo's own `.lokf/` bundle)

The bundle is maintained with [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder), **installed, never committed**; CI installs the librarian skill pinned to a release. Nothing in the application depends on it. To work on the bundle locally:

```bash
npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-librarian --yes   # derive concepts
npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-curator --yes     # confirm them as a person
```

## Before opening a pull request

- **Run the tests**: `uv run pytest lib/test -m "not slow"`. The `slow` marker covers the local-mode CLI runs; CI skips them, so run them by hand when you change how the CLI loads data.
- **Store or data changes**: `just load-store && just validate-store` must not add findings. CI allows exactly today's count (`--allow` in `cli-tests.yml`), which must only go down.
- **Frontend changes**: from `lib/frontend/`, `npm run check` (svelte-check), `npm run lint` (prettier + eslint) and `npm test` must pass, and `npm run build` must produce a production bundle.
- **Knowledge-bundle changes**: `cd .lokf && just lokf-validate` must pass, and `knowledge-registrar.yaml` runs on any `.lokf/**` change. Both keep records well-formed; neither judges whether their content is true.
- **Claims about a framework need a source.** Anything under `byo/` or `graph/` is this project's *interpretation* of a published framework; cite the clause or table you are reflecting, in the PR. [AI_COVENANT.md](AI_COVENANT.md) says why.
- **Lock files are part of the change.** CI checks `uv.lock` and `.lokf/uv.lock` with `--locked`; a dependency edit that does not update its lock fails the run.
- **`lint-and-docs.yaml` is easy to trip locally**: ShellCheck, `actionlint`, markdownlint against `.markdownlint-cli2.jsonc`, link-checking against `lychee.toml`, codespell over every `*.md`, and this file's word budget.
- **Dependabot bumps actions and dependencies** (`.github/dependabot.yml`), never a person. Every action is pinned to a commit SHA, the version in a trailing comment, never to a tag.
- **The skills pin moves with the sidecar copies.** A weekly [`knowledge-sync.yaml`](.github/workflows/knowledge-sync.yaml) pull request moves `TRUST_LADDER_SKILLS_REF` and `TRUST_LADDER_SKILLS_SHA` to the newest release and refreshes every copy it lists; to move sooner, run `.lokf/scripts/knowledge-sync.sh --branch <tag>`. Never move the pin alone: the install step installs nothing when the two disagree.
- **If your change alters behaviour** (not just wording), add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
- Keep changes focused, say what and why, and fill in the PR template's checklist.

## Code of conduct

Participation here is covered by the [Contributor Covenant](CODE_OF_CONDUCT.md).

## Using AI tools

AI assistance is welcome; [AI_COVENANT.md](AI_COVENANT.md) sets the rules, for people and the scheduled `knowledge-librarian` agent alike. You are the author of what you submit, and a claim about what a framework requires must be checked against the framework itself.

## Reporting bugs

Open an issue; the templates ask for your OS, Python version, access pattern, and steps to reproduce.

## Releasing (maintainers)

[docs/releasing.md](docs/releasing.md) says how releases work and why the version stays in `0.x`. The maintainer's steps:

- Write `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) as you go; the release job refuses an empty one (`.github/scripts/changelog-release.mjs check`).
- Type the commit ([Conventional Commits](https://www.conventionalcommits.org/)) for what the change *is*: a user-visible behaviour change is a `feat:` even when most of the diff is prose. Only `feat:`, `fix:` and `security:` commits, and breaking changes, cut a release; other types leave their entries for the next release that does.
- If a PR should release but its commits are typed too quietly, squash-merge it with the right type.
- Every pull request gets a `--dry-run` preview.
- On merge, [`semantic-release.yml`](.github/workflows/semantic-release.yml) retitles the section to `## [X.Y.Z] - YYYY-MM-DD`, writes the version into `pyproject.toml` and `uv.lock` (`.github/scripts/bump-version.mjs`), commits the three files, tags `vX.Y.Z` and publishes the GitHub Release. Once the `KNOWLEDGE_RELEASE_ENABLED` repository variable is `true`, it dispatches [`knowledge-release.yaml`](.github/workflows/knowledge-release.yaml), which attaches the bundle as `knowledge-vX.Y.Z-ai-linkmo.zip` when it changed since the last release that carries one.
- Those steps run behind the `release` GitHub Environment; configure required reviewers on it once, in Settings → Environments, or every qualifying merge ships unattended.
- Below 1.0.0: the `v0.1.0` baseline tag makes the first real release `0.2.0`, and `.releaserc.json` maps `breaking: true` to `minor`. Still mark breaking changes; they show in the release notes. Reaching 1.0.0 means removing that rule in its own PR.
- Leave branch rules for pull requests, required status checks and signed commits off: each would reject the release job's own push, which GitHub does not sign ([repository hardening](https://w3id.org/ktl/docs/threat-model/#repository-hardening) says why). A red check is yours to fix. [Signing your own commits](https://w3id.org/ktl/docs/signing-commits/) is still worth doing.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
