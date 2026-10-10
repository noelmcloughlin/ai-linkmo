# Load the graph into Neo4j

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. These steps fetch the Cypher export that ai-atlas-nexus publishes, start Neo4j in a container, load the file, and open it in the browser. They need the README's [Install](../README.md#install) step done, and `podman` or `docker`; the flags below are the same for both.

## Where the Cypher comes from

This project generates no Cypher of its own. [ai-atlas-nexus](https://github.com/IBM/ai-atlas-nexus) regenerates `graph_export/cypher/ai-risk-ontology.cypher` on every merge and tags each release, so the file at the tag of the installed package is built from the same packaged data the API, the CLI and the web UI serve. `scripts/fetch_cypher.py` downloads that file for the installed version (`importlib.metadata.version("ai-atlas-nexus")`, 1.2.5 at the time of writing) from `https://raw.githubusercontent.com/IBM/ai-atlas-nexus/v<version>/graph_export/cypher/ai-risk-ontology.cypher`. The file is about 2.8 MB and is not committed here; [graph/cypher/README.md](../graph/cypher/README.md) says so for anyone who finds the directory empty.

The saved file starts with three comment lines, which Cypher ignores:

```cypher
// source: https://raw.githubusercontent.com/IBM/ai-atlas-nexus/v1.2.5/graph_export/cypher/ai-risk-ontology.cypher
// ai-atlas-nexus: 1.2.5
// fetched: 2026-10-10
```

A second run reads those lines and downloads again only when the installed version has changed; `--force` downloads regardless, and `--version 1.2.4` fetches another tag. A missing tag or file is reported in one sentence and exits 1.

## Walkthrough

1. **Fetch the Cypher.** Either command writes `graph/cypher/ai-risk-ontology.cypher`; the API's `GET /graph?id=cypher&export=true` does the same and answers with the version and the path.

   ```bash
   just fetch-cypher
   ./ai graph cypher --export
   ```

2. **Start Neo4j**, with `graph/cypher/` mounted where `cypher-shell` can read it. Choose a password.

   ```bash
   podman pull docker.io/library/neo4j
   podman run --name ran_neo4j --rm --volume $(pwd)/graph/cypher:/examples --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/<choose-a-password> docker.io/library/neo4j:latest
   ```

3. **Load the file** from a second terminal.

   ```bash
   podman exec --interactive --tty ran_neo4j cypher-shell -u neo4j -p <your-password>
   :source /examples/ai-risk-ontology.cypher
   ```

4. **Look at it.** Open the [Neo4j Browser](http://localhost:7474/browser/), log in as `neo4j` with your password, and run `CALL db.schema.visualization()`. [byo/images/neo4j.png](../byo/images/neo4j.png) shows what to expect.

## What the file does not contain

**Your own data is not in it.** The artefact is built upstream from the packaged ontology, so the files under `byo/data` cannot appear in the graph. `./ai graph cypher --export --byod` and `GET /graph?id=cypher&export=true&byod=true` are refused with a 400 that says so, rather than returning a file that silently leaves your uploads out. The YAML export, `./ai graph --export --byod`, does include them.

## Known defects in the upstream artefact

These are upstream's to fix, and the owner has reported them with a fix on a branch of IBM/ai-atlas-nexus; a newer tag will carry the fix once it is merged, and `just fetch-cypher` will pick it up when the installed package moves to that version. Nothing here works around them.

- In the owner's count against upstream's current artefact, 3,338 of 9,835 edge statements match no node. Edges point at a slot's declared range label rather than the node's actual label, at enum values (31 edges to `AdapterType`, 129 to `AIUC1EvidenceCategory`) for which no node is ever created, and at six identifiers with no node at all. `cypher-shell` accepts the statements; the `MATCH` finds nothing and the edge is not created.
- Multivalued values are written as Python list representations in a string, such as `"['a', 'b']"`, rather than as Cypher lists.
- Values are interpolated without escaping, so a quote or a backslash inside a description can break a statement.

## The route not taken: RDF

The schema-generic alternative is to stop at RDF. `linkml-convert` writes the same data as Turtle from the LinkML schema with no graph-specific code, and Neo4j's [neosemantics](https://github.com/neo4j-labs/neosemantics) plugin imports that losslessly, with `rdf:type` as labels and multivalued literals as arrays. It would remove the defects above and serve any triplestore, at the cost of a plugin install on a self-hosted Neo4j, a `uri` property on every node, and shortened property names. It is the alternative on record, and is not built.

The graph door is the fourth of the four access patterns; [byo/notes/EXAMPLES.md](../byo/notes/EXAMPLES.md) walks through all four with a real incident.
