# Build steps that derive checked-in files from the schema and the exposure file.
#
# Each recipe writes something the repository keeps under version control, so that a reader
# sees the current contract, UI list or graph without running the server. Run `just --list`
# to see them. The knowledge-bundle recipes live in .lokf/justfile.

# List available recipes
default:
    @just --list

# Write the API contract, FastAPI's /openapi.json, to docs/openapi.json without a server.
gen-openapi:
    uv run python scripts/export_openapi.py docs/openapi.json

# Write lib/frontend/src/lib/entities.json, the web UI's entity list, from the exposure file.
gen-ui-config:
    uv run python scripts/gen_ui_config.py lib/frontend/src/lib/entities.json

# Fetch the Cypher export that ai-atlas-nexus commits, pinned to the installed version.
fetch-cypher:
    uv run python scripts/fetch_cypher.py graph/cypher/ai-risk-ontology.cypher
