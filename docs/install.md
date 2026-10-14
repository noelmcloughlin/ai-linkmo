# Install

This page says what AI-LinkMO needs on the machine, how to install it, and how to start the API, the web UI and the CLI. [Working with the data](working-with-the-data.md) says what to do next.

> **Prefer to ask?** Install the docent skill into any agent you already use (`npx skills add noelmcloughlin/knowledge-trust-ladder --skill ktl-docent --yes`) and ask it about this project, such as *where the EU AI Act encoding comes from, and who checked it*. It answers from this repository's own bundle and says how far each answer has been checked.

## Install

Python 3.11+ and [uv](https://docs.astral.sh/uv/); Node 22 for the web UI.

```bash
uv sync --extra test
./ai --help
```

That is the offline CLI, ready to use. If `uv sync` needs to compile anything on your machine, or you have upgraded `ai-atlas-nexus` and need to regenerate the UI's schema, see [docs/install-notes.md](install-notes.md).

## Quick start

1. **Start the API** ([details](../lib/api/README.md)). It listens on port 8000. Its write endpoints are not authenticated, so keep it on localhost.

   ```bash
   uv run uvicorn lib.api.server:app --reload
   ```

2. **Start the web UI** in a second terminal ([details](../lib/frontend/README.md)). The login in the top corner is a persona picker for the demo, not authentication. **Curate mode**, which edits records in your own data files, sits behind it.

   ```bash
   cd lib/frontend
   npm ci
   npm run dev
   ```

3. **Try the CLI** in a third terminal ([details](../lib/cli/README.md)). Every entity type is one command away; [docs/cli-examples.md](cli-examples.md) lists them all.

   ```bash
   ./ai -h
   ./ai risk -h
   ```

From there, bring your own data, compute a crosswalk, search the records, browse them in Datasette, or load the graph into Neo4j: [docs/working-with-the-data.md](working-with-the-data.md).
