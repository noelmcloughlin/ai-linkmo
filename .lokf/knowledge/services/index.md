# Services

The four AI-LinkMO access patterns:

* [AI-LinkMO CLI](cli.md) - The command-line tool (`./ai`) for querying AI governance data such as risks, taxonomies, controls, models, evaluations and crosswalks. The linkmo project generates it, with one command per class its exposure file names and one option per slot of that class in the LinkML schema.
* [FastAPI Backend](fastapi-backend.md) - The REST API serving AI governance data to the CLI, the web UI and external GRC tooling. The linkmo project in `ai-risk-ontology-linkmo/` generates its endpoints from the exposure file and the LinkML schema, and its contract is the server's `/openapi.json`.
* [Svelte Web UI](web-ui.md) - Vite + Svelte 5 single-page application for exploring AI governance data through the FastAPI backend, aimed at non-technical stakeholders.
* [Neo4j Graph Database](graph-db.md) - Graph-database access pattern - the exported knowledge graph is loaded into Neo4j via Cypher for relationship analysis and regulatory crosswalks.
* [Datasette browse UI](datasette-browse.md) - Datasette over SQLite databases built from the schema's gen-sqltables tables, one of the packaged data and one with the bring-your-own data added, served on port 8001 with schema-derived descriptions, facets, search and JSON and CSV exports.
