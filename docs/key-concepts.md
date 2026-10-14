# Key concepts, in plain English

[The architecture page](architecture.md#one-model-four-ways-in) shows the four doors. These are the words they share. A term means the same thing at every door, because every door is generated from the same [ontology](https://ibm.github.io/ai-atlas-nexus/ontology/).

| Term | What it means |
| :--- | :--- |
| **Taxonomy** | A framework's catalogue of risks and controls (for example NIST AI RMF, FINOS AIGF) |
| **Risk** | A named, identified harm (for example `atlas-toxic-output`, `nist-confabulation`) |
| **Control / Action** | Something you do or deploy to detect or mitigate a risk |
| **Obligation** | A requirement a framework imposes, with evidence categories describing how you prove it |
| **Crosswalk** | A machine-generated mapping of equivalent concepts *between* frameworks |
| **Incident** | A realised risk, something that happened (for example `ibm-risk-atlas-ri-fake-legal-cases`), linked back to the risks it demonstrates |
| **Evaluation** | A benchmark or test that measures a risk or a capability (for example `ai_eval_PopQA`), linked to the datasets and tasks it uses |
| **BYOD** | Bring Your Own Data: your internal policies encoded in the same schema, queryable alongside the open data |

Every entity type is one CLI command away; [cli-examples.md](cli-examples.md) lists them all. Adding your own records under these terms is [working-with-the-data.md](working-with-the-data.md).
