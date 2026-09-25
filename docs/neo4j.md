# Load the graph into Neo4j

Governance data is a graph: risks relate to controls, controls implement obligations, obligations trace to frameworks. These steps export the ontology and its data as Cypher, start Neo4j in a container, load the export, and open it in the browser. They need the README's [Install](../README.md#install) step done, and `podman` or `docker`; the flags below are the same for both.

1. **Export the Cypher.** This writes `graph/cypher/ai-risk-ontology.cypher`. The export reads the packaged ontology only, so it shows the open frameworks; `--byod` does not add your uploads to it ([Status and caveats](status.md)). The repository commits the output, so this step is optional unless you want it fresh.

   ```bash
   ./ai graph cypher --export --byod
   ```

2. **Start Neo4j**, with `graph/cypher/` mounted where `cypher-shell` can read it. Choose a password.

   ```bash
   podman pull docker.io/library/neo4j
   podman run --name ran_neo4j --rm --volume $(pwd)/graph/cypher:/examples --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/<choose-a-password> docker.io/library/neo4j:latest
   ```

3. **Load the export** from a second terminal.

   ```bash
   podman exec --interactive --tty ran_neo4j cypher-shell -u neo4j -p <your-password>
   :source /examples/ai-risk-ontology.cypher
   ```

4. **Look at it.** Open the [Neo4j Browser](http://localhost:7474/browser/), log in as `neo4j` with your password, and run `CALL db.schema.visualization()`. [byo/images/neo4j.png](../byo/images/neo4j.png) shows what to expect.

The graph door is the fourth of the four access patterns; [byo/notes/EXAMPLES.md](../byo/notes/EXAMPLES.md) walks through all four with a real incident.
