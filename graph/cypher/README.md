# Cypher export

`ai-risk-ontology.cypher` is not committed. It is the Cypher export that [ai-atlas-nexus](https://github.com/IBM/ai-atlas-nexus) publishes at `graph_export/cypher/ai-risk-ontology.cypher`, fetched at the release tag of the installed package:

```bash
just fetch-cypher
```

The saved file starts with three `//` comment lines naming its source URL, its ai-atlas-nexus version and the fetch date. [docs/neo4j.md](../../docs/neo4j.md) loads it into Neo4j and lists what the artefact does and does not contain.
