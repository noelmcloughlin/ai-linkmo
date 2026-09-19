# Contributing to AI-LinkMO

Thanks for your interest in improving AI-LinkMO!

## What this project is

AI-LinkMO demonstrates four ways into one linked AI-governance knowledge graph: a CLI (`./ai`), an HTTP API, a Svelte web UI, and direct graph queries. Most contributions touch exactly one of those paths, plus the data underneath them.

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

`byo/data/` holds the encoded governance frameworks the graph is built from. `byo/notes/EXAMPLES.md` walks through the four access patterns, and the `bring-your-own-data` playbook in the knowledge bundle explains the format. Tests that need those files are marked `byod_required`.

### Agent skills (optional - only for editing this repo's own `.lokf/` bundle)

Nothing in the application depends on any agent skill, and no user of the CLI, API, or UI needs one. The skills below concern one thing only: this repository's own `.lokf/knowledge/` bundle, the documentation-about-this-repo that CI keeps in step with the source. Skip this section unless you are editing that.

The bundle is maintained with [knowledge-trust-ladder](https://github.com/noelmcloughlin/knowledge-trust-ladder), **installed, never committed** - `.agents/`, `.claude/`, and `skills-lock.json` are git-ignored, and CI installs the librarian skill itself at run time, pinned to a release. To work on the bundle locally:

```bash
npx skills add noelmcloughlin/knowledge-trust-ladder --skill lokf-librarian --yes   # derive concepts
npx skills add noelmcloughlin/knowledge-trust-ladder --skill lokf-curator --yes     # confirm them as a person
```

`lokf-sidecar` is only for re-generating the `.lokf/` tooling and the two bundle workflows from their template (rare); `lokf-docent` only lets an agent answer questions from the bundle. Neither is needed to contribute.

## Before opening a pull request

- **Run the tests**: `uv run pytest lib/test -m "not slow"`. The `slow` marker covers local-mode CLI runs that each spawn a fresh interpreter and load the full ontology (~25 minutes); CI skips them too, so run them by hand when you have changed how the CLI loads data.
- **Frontend changes**: from `lib/frontend/`, `npm run check` (svelte-check), `npm run lint` (prettier + eslint), and `npm test` must all pass, and `npm run build` must produce a production bundle.
- **Knowledge-bundle changes**: `cd .lokf && just lokf-validate` must pass. The registrar keeps records well-formed; it never judges whether their content is true.
- **Claims about a framework need a source.** Anything under `byo/` or `graph/` is this project's *interpretation* of a published framework. Cite the clause or table you are reflecting, in the PR. See [AI_COVENANT.md](AI_COVENANT.md) for why this one matters more here than in most repositories.
- **Lock files are part of the change.** `uv.lock` and `.lokf/uv.lock` are checked with `--locked` in CI, so a dependency edit that does not update its lock fails the run. Commit both.
- **Two CI gates are easy to trip locally**: `lint-and-docs.yaml` (ShellCheck, `actionlint`, markdownlint against `.markdownlint-cli2.jsonc`, link-checking against `lychee.toml`, and codespell over every `*.md`) and, on any `.lokf/**` change, `knowledge-registrar.yaml`. If you touched a workflow or a shell script, expect ShellCheck and `actionlint` to have an opinion.
- **Pinned action SHAs and dependencies are bumped by Dependabot** (`.github/dependabot.yml`), not by hand - don't float a pin to a tag to get a newer version. Every action in every workflow is pinned to a commit SHA with the version in a trailing comment; keep that convention when adding one.
- **If your change alters behaviour** (not just wording), add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md). The release pipeline refuses to run on an empty one - it releases only what has already been written up.
- Keep changes focused; describe what and why in the PR. The PR template's checklist is the short version of this section - fill it in rather than deleting it.

## Layout notes

- `ai` is a thin bash entry point that runs `lib/cli` through `uv run`, so the CLI needs no separate install step.
- Test configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`, including the `slow` and `byod_required` markers. `pytest-timeout` is available but no default timeout is set.
- `.lokf/` is a sidecar: a knowledge bundle kept *beside* the code it documents, in the same repository. `.lokf/README.md` explains the layout.

## Code of conduct

Participation here is covered by the [Contributor Covenant](CODE_OF_CONDUCT.md), the same one the sibling LOKF projects use.

## Using AI tools

AI assistance is welcome here - this repository's own `.lokf/` bundle is maintained by an agent. What that requires of you is unchanged: you are the author of whatever you submit, you are responsible for understanding and defending it in review, and an agent may not participate in discussion on your behalf. Because this project encodes governance frameworks that people may rely on, an AI-drafted claim about what a framework requires must be checked against the framework itself before you submit it. The full rules, including how this repo's own scheduled `knowledge-librarian` agent is held to them, are in [AI_COVENANT.md](AI_COVENANT.md).

## Reporting bugs

Open an issue with your OS, Python version, which access pattern you used, and steps to reproduce. The issue templates ask for exactly this.

## Releasing (maintainers)

The version number is not hand-picked. Write `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) as you go and describe what changed, with a [Conventional Commits](https://www.conventionalcommits.org/) type on the commit. Open the PR as normal.

**Only `feat:`, `fix:` and `security:` cut a release.** `docs:`, `chore:`, `refactor:`, `style:` and `test:` deliberately do not: a branch carrying only those merges cleanly, releases nothing, and leaves its `## [Unreleased]` entries to ship with the next release that does. Type the commit for what the change *is* - a user-visible behaviour change is a `feat:` even when most of the diff is prose. If a PR should release and its commits are typed too quietly, squash-merge it and give the squash commit the right type.

### This project stays below 1.0.0

AI-LinkMO is a demo, and its OpenAPI spec, web UI and CLI are all expected to change shape. Two things keep the version in `0.x`, and both are deliberate:

- **The `v0.1.0` baseline tag.** semantic-release defaults a repository's *first* release to `1.0.0` when no tag exists. The baseline tag gives it somewhere to count from, so the first real release is `0.2.0`.
- **A breaking change bumps the minor version, not the major one.** `.releaserc.json` maps `breaking: true` to `minor`, so a `BREAKING CHANGE:` footer takes `0.4.0` to `0.5.0` rather than to `1.0.0`.

Reaching 1.0.0 is therefore a deliberate act: remove that rule from `.releaserc.json` in its own PR, when the interfaces are ones this project is prepared to keep. Until then, a breaking change is still worth marking - it shows up in the release notes and tells readers what moved.

### What happens on merge

[`semantic-release.yml`](.github/workflows/semantic-release.yml) does the rest:

1. Computes the next version from the commits since the last tag. Nothing lands if none of them warrant one.
2. Refuses to proceed if `## [Unreleased]` is empty (`.github/scripts/changelog-release.mjs check`).
3. Retitles that section to `## [X.Y.Z] - YYYY-MM-DD` with a fresh empty one above it, and writes the version into `pyproject.toml` and `uv.lock` (`.github/scripts/bump-version.mjs` - there is no Python equivalent of `@semantic-release/npm`, and editing the lock's one version line in place keeps `uv` out of the release runner).
4. Commits those three files, creates the `vX.Y.Z` tag, and publishes a GitHub Release whose notes are the promoted section.

Every pull request into `main` also gets a `--dry-run` preview of all of this, so a broken commit message or a broken script is caught in review rather than after merge.

Step 3 onward runs behind the `release` GitHub Environment - **configure required reviewers on it once, in this repository's Settings → Environments**, or every qualifying merge ships unattended.

### What the repository settings mean for you

- **Changes reach `main` by pull request, but the rule is not enforced by a ruleset.** A ruleset that requires pull requests rejects every direct push, and the release job's own push - the changelog promotion and tag in step 4 - cannot be exempted from it: a ruleset bypass list accepts roles, teams, GitHub Apps and Dependabot, and `github-actions[bot]` is none of those. So the pull-request discipline here is a convention, held to by the maintainer, not a gate. Open one anyway. Required status checks are off for the same reason - that rule is applied to direct pushes too, and rejects the release job's `[skip ci]` commit for having no checks of its own. CI still runs on every pull request and is still read before merge; it is just not the thing that blocks one, so treat a red check as your problem to fix rather than a net that will catch it.
- **"Require signed commits" as a branch rule is deliberately off**, and must stay off. A `git commit` made inside a runner is unsigned - GitHub only auto-signs commits made through the web UI or API, and `@semantic-release/git` uses the git CLI. Turning the rule on would reject step 4 and break every release. Signing your own commits locally is a different thing, nothing gates on it here, and it is still worth doing: [`knowledge-trust-ladder`](https://github.com/noelmcloughlin/knowledge-trust-ladder/blob/main/docs/signing-commits.md) walks through GPG and SSH setup, and how to renew a GPG key before it expires.

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE), the license this project ships under.
