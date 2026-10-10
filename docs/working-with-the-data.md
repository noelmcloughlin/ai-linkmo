# Working with the data: bring your own, crosswalk, search, graph

[The README's Quick start](../README.md#quick-start) gets the API, the web UI and the CLI running. These are the four things to do next with the data.

## Bring your own data

The open frameworks are the starting point. The value comes when your **internal** policies, taxonomies and controls live in the same model, so one query spans public regulation and private practice.

Add schema-compliant YAML files to [byo/data](../byo/data); the [upstream readme](https://github.com/IBM/ai-atlas-nexus/blob/main/src/ai_atlas_nexus/ai_risk_ontology/util/README.md) says what the schema expects, and the nine encodings already there, [FINOS](../byo/data/finos-aigf.yaml) first, show the shape. Validate a contributed file against the schema:

```bash
SDIR="$(uv run python -c 'import ai_atlas_nexus, pathlib; print(pathlib.Path(ai_atlas_nexus.__file__).parent / "ai_risk_ontology" / "schema")')"
uv run linkml validate byo/data/*.yaml -s "${SDIR}/ai-risk-ontology.yaml"
```

Pass `--byod` to any `./ai` command to query your files alongside the packaged data. **Curate mode** in the web UI adds, edits and deletes records in those same files from the browser.

## Crosswalk

A crosswalk is computed from the data, not kept by hand in a spreadsheet. That is where linked data pays off for a compliance team. The `./ai` command maps the risks in one taxonomy onto another, finds the related risks, and shows a subset of the risk content as a pandas dataframe:

```bash
./ai crosswalk --isDefinedByTaxonomy nist-ai-rmf --isDefinedByTaxonomy2 finos-aigf --export --byod
```

## Search and dumps

The store has a text index. `just load-store` builds the store and `just index-store` builds the index, a trigram index over each record's id, name and description kept in the same DuckDB files, in about half a minute for the packaged data and one minute for the set with your files. Then:

```bash
./ai search --q 'toxic output' --scope risk
```

`--scope` names one scope, `control` say, and covers its subclasses; without it every exposed class is searched. `--limit` cuts the list, 20 by default, and `--byod` searches the store that includes your files. The same operation is `GET /search?q=toxic+output&scope=risk`; each item is the record with its `score` and `type`. A scope whose index is missing answers 409 and says to run `just index-store`; run it again after `just load-store`, which rebuilds the files without the index.

`just dump-store` writes the store as YAML under `lib/store/data/dump`, `atlas.yaml` and `byod.yaml`, one key per class with its records under it, so the merged view of the data can be read or diffed without DuckDB. `uv run python scripts/dump_store.py <dir> --format json` writes JSON instead.

## Graph database

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. The project generates no Cypher of its own; one command fetches the Cypher export that ai-atlas-nexus publishes, at the release tag of the installed package:

```bash
just fetch-cypher
```

`./ai graph cypher --export` does the same through the API. The artefact is built upstream from the packaged ontology, so it shows the open frameworks and cannot include your uploads; `--byod` is refused there rather than ignored ([Status and caveats](status.md)). To load it into Neo4j in a container and look at it in the browser, with the artefact's provenance header and known defects: [neo4j.md](neo4j.md).
