# Build steps that derive files from the schema, the exposure file and the data.
#
# gen-openapi and gen-ui-config write files the repository keeps under version control, so
# that a reader sees the current contract or UI list without running the server. The others
# build local artefacts that are never committed, such as the graph export, the DuckDB store,
# the browse database and the schema's pages. Run `just --list` to see them. The
# knowledge-bundle recipes live in .lokf/justfile.

# The linkmo project in ai-risk-ontology-linkmo/ builds the contract, the entity list, the
# browse databases and the schema's pages. It is a member of this project's uv workspace,
# so its recipes run on this project's environment, which has ai-atlas-nexus already.
host := "uv run --project '" + justfile_directory() + "'"
export LINKMO_PYTHON := env("LINKMO_PYTHON", host + " python")
export LINKMO_BROWSE_PYTHON := env("LINKMO_BROWSE_PYTHON", host + " --extra browse python")
export LINKMO_DATASETTE := env("LINKMO_DATASETTE", host + " --extra browse datasette")
export LINKMO_GEN_DOC := env("LINKMO_GEN_DOC", host + " gen-doc")
linkmo := just_executable() + " --justfile ai-risk-ontology-linkmo/justfile"

# List available recipes
default:
    @just --list

# Write the API contract, FastAPI's /openapi.json, to docs/openapi.json without a server.
gen-openapi:
    {{ linkmo }} gen-openapi

# Write lib/frontend/src/lib/entities.json, the web UI's entity list, from the exposure file.
gen-ui-config:
    {{ linkmo }} gen-ui-config

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

# Build the SQLite database and its Datasette metadata under ai-risk-ontology-linkmo/browse.
build-browse:
    {{ linkmo }} build-browse

# Build the same database with the bring-your-own data added, under ai-risk-ontology-linkmo/browse-byod.
build-browse-byod:
    {{ linkmo }} build-browse --data-dir browse-byod --param byod=true

# Serve the browse database with Datasette on http://127.0.0.1:8001, building it if it is missing.
browse:
    {{ linkmo }} browse

# Serve the database with the bring-your-own data on http://127.0.0.1:8001, building it if it is missing.
browse-byod:
    test -f ai-risk-ontology-linkmo/browse-byod/metadata.yaml || just build-browse-byod
    {{ linkmo }} browse browse-byod

# Write one example per class with records to ai-risk-ontology-linkmo/docs/elements/examples.
gen-examples:
    {{ linkmo }} gen-examples

# Write the schema's pages to ai-risk-ontology-linkmo/docs/elements, each with its example.
gen-doc:
    {{ linkmo }} gen-doc
