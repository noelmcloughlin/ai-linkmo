# Contributing to AI-LinkMO

Thanks for your interest in improving AI-LinkMO!

## What this project is

AI-LinkMO demonstrates four ways into one linked AI-governance knowledge graph: a CLI (`./ai`), an HTTP API, a Svelte web UI, and direct graph queries.

| Path | Lives in |
| --- | --- |
| CLI | `ai`, `lib/cli/` |
| HTTP API | `lib/api/` |
| Web UI | `lib/frontend/` |
| Graph, ontology, crosswalks | `graph/`, `byo/` |
| Tests | `lib/test/` |
| This repo's own knowledge bundle | `.lokf/knowledge/` |

## Development setup

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required; Node 22 for the frontend.

```bash
git clone https://github.com/noelmcloughlin/ai-linkmo.git
cd ai-linkmo
uv sync --extra test        # application + test dependencies
./ai --help                 # runs lib/cli via uv
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

The skills below concern only this repository's own `.lokf/knowledge/` bundle, which CI keeps in step with the source; nothing in the application depends on them.

The bundle is maintained with [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder), **installed, never committed**; CI installs the librarian skill at run time, pinned to a release. To work on the bundle locally:

```bash
npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-librarian --yes   # derive concepts
npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-curator --yes     # confirm them as a person
```

`ktl-sidecar` regenerates the `.lokf/` tooling and the two bundle workflows from their template; `ktl-docent` lets an agent answer questions from the bundle. Neither is needed to contribute.

## Before opening a pull request

- **Run the tests**: `uv run pytest lib/test -m "not slow"`. The `slow` marker covers the local-mode CLI runs; CI skips them, so run them by hand when you change how the CLI loads data.
- **Frontend changes**: from `lib/frontend/`, `npm run check` (svelte-check), `npm run lint` (prettier + eslint) and `npm test` must pass, and `npm run build` must produce a production bundle.
- **Knowledge-bundle changes**: `cd .lokf && just lokf-validate` must pass. The registrar keeps records well-formed; it never judges whether their content is true.
- **Claims about a framework need a source.** Anything under `byo/` or `graph/` is this project's *interpretation* of a published framework; cite the clause or table you are reflecting, in the PR. [AI_COVENANT.md](AI_COVENANT.md) says why.
- **Lock files are part of the change.** CI checks `uv.lock` and `.lokf/uv.lock` with `--locked`; a dependency edit that does not update its lock fails the run. Commit both.
- **Two CI gates are easy to trip locally**: `lint-and-docs.yaml` (ShellCheck, `actionlint`, markdownlint against `.markdownlint-cli2.jsonc`, link-checking against `lychee.toml`, and codespell over every `*.md`) and, on any `.lokf/**` change, `knowledge-registrar.yaml`.
- **Pinned action SHAs and dependencies are bumped by Dependabot** (`.github/dependabot.yml`), not by hand; do not float a pin to a tag. Every action is pinned to a commit SHA with the version in a trailing comment; keep that convention.
- **The skills pin moves with the sidecar copies.** When moving `TRUST_LADDER_SKILLS_REF` in [`knowledge-librarian.yaml`](.github/workflows/knowledge-librarian.yaml), copy `knowledge-registrar.yaml`, `knowledge-release.yaml` and the scripts under `.lokf/scripts/` from that release's `skills/ktl-sidecar/templates/` in the same pull request: the pin alone changes only the skill the scheduled run installs. `knowledge-librarian.yaml` carries local changes, so compare it by hand.
- **If your change alters behaviour** (not just wording), add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
- Keep changes focused, say what and why, and fill in the PR template's checklist.

## Layout notes

- Test configuration, including the `slow` and `byod_required` markers, lives in `pyproject.toml` under `[tool.pytest.ini_options]`. `pytest-timeout` is available but no default timeout is set.
- `.lokf/README.md` explains the sidecar's layout.

## Code of conduct

Participation here is covered by the [Contributor Covenant](CODE_OF_CONDUCT.md), the same one the sibling LOKF projects use.

## Using AI tools

AI assistance is welcome, and [AI_COVENANT.md](AI_COVENANT.md) sets the rules. You are the author of what you submit and defend it in review; an agent may not speak for you in discussion. A claim about what a framework requires must be checked against the framework itself. The same rules hold for this repository's scheduled `knowledge-librarian` agent.

## Reporting bugs

Open an issue; the templates ask for your OS, Python version, access pattern, and steps to reproduce.

## Releasing (maintainers)

[README.md#releases](README.md#releases) says how releases work and why the version stays in `0.x`. The maintainer's steps:

- Write `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) as you go; the release job refuses an empty one (`.github/scripts/changelog-release.mjs check`).
- Type the commit ([Conventional Commits](https://www.conventionalcommits.org/)) for what the change *is*: a user-visible behaviour change is a `feat:` even when most of the diff is prose. Only `feat:`, `fix:` and `security:` cut a release; `docs:`, `chore:`, `refactor:`, `style:` and `test:` leave their entries for the next release that does.
- If a PR should release but its commits are typed too quietly, squash-merge it with the right type.
- Every pull request gets a `--dry-run` preview.
- On merge, [`semantic-release.yml`](.github/workflows/semantic-release.yml) retitles the section to `## [X.Y.Z] - YYYY-MM-DD` with a fresh empty one above it, and writes the version into `pyproject.toml` and `uv.lock` (`.github/scripts/bump-version.mjs`). It commits those three files, tags `vX.Y.Z`, and publishes the GitHub Release. Once the `KNOWLEDGE_RELEASE_ENABLED` repository variable is `true`, it then dispatches [`knowledge-release.yaml`](.github/workflows/knowledge-release.yaml), which attaches the knowledge bundle to that release as `knowledge-vX.Y.Z-ai-linkmo.zip` when the bundle changed since the last release that carries one.
- Those steps run behind the `release` GitHub Environment; configure required reviewers on it once, in Settings → Environments, or every qualifying merge ships unattended.
- Below 1.0.0: the `v0.1.0` baseline tag makes the first real release `0.2.0`, and `.releaserc.json` maps `breaking: true` to `minor`. Still mark breaking changes; they show in the release notes. Reaching 1.0.0 means removing that rule in its own PR.
- Pull requests to `main` are a convention, not a ruleset, and required status checks are off; either rule would reject the release job's own push ([SECURITY.md](SECURITY.md#repository-hardening) says why). A red check is yours to fix.
- "Require signed commits" as a branch rule must stay off: the release job commits through the git CLI in a runner, which GitHub does not sign. Signing your own commits is separate and still worth doing; [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/signing-commits.md) covers GPG and SSH setup and renewing a GPG key.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE), which this project ships under.
