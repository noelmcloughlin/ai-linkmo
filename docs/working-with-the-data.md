# Working with the data: bring your own, crosswalk, graph

[The README's Quick start](../README.md#quick-start) gets the API, the web UI and the CLI running. These are the three things to do next with the data.

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

## Graph database

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. One command exports the schema and the data as Cypher:

```bash
./ai graph cypher --export --byod
```

The export reads the packaged ontology, so it shows the open frameworks; `--byod` does not add your uploads to it ([Status and caveats](status.md)). To load it into Neo4j in a container and look at it in the browser: [neo4j.md](neo4j.md).
