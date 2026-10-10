# Build steps that derive files from the schema, the exposure file and the data.
#
# gen-openapi and gen-ui-config write files the repository keeps under version control, so
# that a reader sees the current contract or UI list without running the server. The others
# build local artefacts that are never committed, such as the graph export, the DuckDB store
# and the browse databases. Run `just --list` to see them. The knowledge-bundle recipes live
# in .lokf/justfile.

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

# Load the packaged and bring-your-own data into the DuckDB store under lib/store/data.
load-store:
    uv run python scripts/load_store.py

# Validate every collection of the store against the schema and report findings as JSON.
validate-store:
    uv run python scripts/validate_store.py lib/store/data/config.yaml

# Build the trigram search indexes of the store's collections.
index-store:
    uv run python scripts/index_store.py

# Dump the store as YAML under lib/store/data/dump, one file per database.
dump-store:
    uv run python scripts/dump_store.py lib/store/data/dump

# Build the SQLite databases and the Datasette metadata under lib/browse/data.
build-browse:
    uv run --extra browse python scripts/build_browse.py

# Serve lib/browse/data with Datasette on http://127.0.0.1:8001, building it first if it is missing.
browse:
    test -f lib/browse/data/metadata.yaml || just build-browse
    uv run --extra browse datasette serve lib/browse/data
