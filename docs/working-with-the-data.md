# Working with the data: bring your own, crosswalk, search, browse, graph

[The README's Quick start](../README.md#quick-start) gets the API, the web UI and the CLI running. These are the things to do next with the data.

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

## Browse the data

[Datasette](https://datasette.io/) gives every class a table you can filter, facet, search and export. Two recipes set it up:

```bash
just build-browse
just browse
```

`just build-browse` writes two SQLite databases under `lib/browse/data`: `atlas.sqlite` holds the packaged data and `byod.sqlite` adds your files from `byo/data`. It takes about twenty seconds the first time and ten after that, because the table definitions are kept until the schema changes. `just browse` serves them on <http://127.0.0.1:8001>, and builds them first if they are missing. Both recipes install the `browse` extra, Datasette and sqlite-utils, through uv.

The tables follow the schema. LinkML's `gen-sqltables` generator makes one table per class, abstract parents included, and a link table such as `Risk_hasRelatedAction` for each multivalued slot. Each record is written to its own class's table and to the table of every class above it, so `Taxonomy` lists every taxonomy, whatever its class. A reference points at the table of the class its slot names. A risk's taxonomy therefore links to that taxonomy's row in `Taxonomy`, and the risks that cite it are listed under *Links from other tables* on that row, not on its `RiskTaxonomy` row. Empty class tables are hidden behind the *hidden tables* link, and empty link tables are left out.

`lib/browse/data/metadata.yaml` is written from the schema in the same build. It describes each table and column from its class and slot, shows each record by its name wherever another row links to it, and offers facets on enum and reference columns with few values. Search covers each table's name and description, and every page has a JSON and a CSV form. The build lists the references that name a record the data does not hold, such as 20 risks whose risk group is missing.

A database's front page takes two or three seconds, since Datasette looks at each of its few hundred tables; table and row pages answer at once.

## The schema's pages, with examples

`just gen-doc` writes the schema's pages to `docs/elements` with LinkML's `gen-doc`, one page per class, slot, enum and type. Each class page has an *Examples* section with a record from the data: for every concrete class that has records, the record whose identifier sorts first. `just gen-examples`, which `just gen-doc` runs first, writes those examples to `docs/elements/examples` and validates each against its class, and the recipe stops if one fails. Abstract classes get no example, although the data holds a few records of `Certification`, `Group` and `Taxonomy`. Nothing under `docs/elements` is committed.

## Graph database

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. The project generates no Cypher of its own; one command fetches the Cypher export that ai-atlas-nexus publishes, at the release tag of the installed package:

```bash
just fetch-cypher
```

`./ai graph cypher --export` does the same through the API. The artefact is built upstream from the packaged ontology, so it shows the open frameworks and cannot include your uploads; `--byod` is refused there rather than ignored ([Status and caveats](status.md)). To load it into Neo4j in a container and look at it in the browser, with the artefact's provenance header and known defects: [neo4j.md](neo4j.md).
