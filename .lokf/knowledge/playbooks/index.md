# Playbooks

* [Knowledge sources map](knowledge-sources.md) - The librarian's scrape map: every repository location and external URL this bundle derives concepts from, and how to re-verify each on a refresh run.
* [Install and run AI-LinkMO](install-and-run.md) - How to install AI-LinkMO and start its four doors (the CLI, the FastAPI backend, the Svelte web UI and the Neo4j graph database), then build the store, search it, browse it in Datasette and run the tests.
* [Bring your own data (BYOD)](bring-your-own-data.md) - How to add institutional governance data: schema-compliant YAML dropped into byo/data/ is picked up by the CLI, API and web UI with --byod, and by the YAML graph export, the store and the browse UI; the Cypher export refuses --byod.
