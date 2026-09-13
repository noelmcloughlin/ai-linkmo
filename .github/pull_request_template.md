## Summary

## What changed?

- [ ] Application code (`lib/api/`, `lib/cli/`, `ai`) - behaviour of the CLI or API
- [ ] Frontend (`lib/frontend/`) - the Svelte web UI
- [ ] Graph, ontology, or crosswalk data (`graph/`, `byo/`)
- [ ] This repo's own `.lokf/knowledge/` bundle (documentation *about this repo*)
- [ ] Repository packaging only (CI, templates, docs unrelated to behaviour)

## Checklist

- [ ] `uv run pytest lib/test -m "not slow"` passes locally
- [ ] Slow tests (`-m slow`, the local-mode CLI runs) were considered - say here if they were skipped and why
- [ ] Frontend changes: `npm install; npm run check`, `npm run lint`, and `npm test` pass in `lib/frontend/`
- [ ] If `.lokf/` changed, `cd .lokf && just lokf-validate` passes
- [ ] Any new claim about the project is reflected in the knowledge bundle, or deliberately left for the librarian

## AI Assistance

If you used AI tools while preparing this PR, you are still the author and responsible for understanding, verifying, and defending your submission. Please engage with reviewers personally rather than through your agent during feedback and revisions. Don't dump LLM output into this PR without curation. See the [AI Covenant](../AI_COVENANT.md) for details.
