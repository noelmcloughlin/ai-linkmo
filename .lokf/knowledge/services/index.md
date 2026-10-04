# Services

The four AI-LinkMO access patterns:

* [AI-LinkMO CLI](cli.md) - Command-line tool (./ai) for querying AI governance data - risks, taxonomies, controls, models, evaluations, crosswalks - built dynamically from the OpenAPI specification.
* [FastAPI Backend](fastapi-backend.md) - REST API serving AI governance data to the CLI, web UI, and external GRC tooling; endpoints are generated dynamically from the OpenAPI specification.
* [Svelte Web UI](web-ui.md) - Vite + Svelte 5 single-page application for exploring AI governance data through the FastAPI backend, aimed at non-technical stakeholders.
* [Neo4j Graph Database](graph-db.md) - Graph-database access pattern - the exported knowledge graph is loaded into Neo4j via Cypher for relationship analysis and regulatory crosswalks.
