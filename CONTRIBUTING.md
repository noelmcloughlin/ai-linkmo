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

The bundle is maintained with [lokf-agent-skills](https://github.com/noelmcloughlin/lokf-agent-skills), **installed, never committed** - `.agents/`, `.claude/`, and `skills-lock.json` are git-ignored, and CI installs the librarian skill itself at run time, pinned to a release. To work on the bundle locally:

```bash
npx skills add noelmcloughlin/lokf-agent-skills --skill lokf-librarian --yes   # derive concepts
npx skills add noelmcloughlin/lokf-agent-skills --skill lokf-curator --yes     # confirm them as a person
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

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE), the license this project ships under.
