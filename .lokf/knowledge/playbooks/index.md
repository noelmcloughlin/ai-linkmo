# Playbooks

* [Knowledge sources map](knowledge-sources.md) - The librarian's scrape map - every repository location and external URL this bundle derives concepts from, and how to re-verify each on a refresh run.
* [Install and run AI-LinkMO](install-and-run.md) - How to build the environment and start each of the four access patterns - CLI, FastAPI backend, Svelte web UI, and Neo4j graph database.
* [Bring your own data (BYOD)](bring-your-own-data.md) - How to add institutional governance data - schema-compliant YAML dropped into byo/data/ is picked up by the CLI, API and web UI with --byod, and by the YAML graph export, but not the Cypher export.
