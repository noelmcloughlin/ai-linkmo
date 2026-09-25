# CLI examples: every entity type, one command away

Most of the commands below are test cases in [lib/test/test_cli_examples.py](../lib/test/test_cli_examples.py), run in both API mode and local mode. `--count` prints the number of matches; drop it to see the records. The CLI is generated from [lib/api/openapi.yaml](../lib/api/openapi.yaml), so `./ai <scope> -h` always shows the current flags.

A few flags recur. `--byod` adds the bring-your-own-data frameworks under `byo/data/` to the packaged ontology (see [Bring your own data](working-with-the-data.md#bring-your-own-data)). `--related` returns the related records; `--related_ids` returns only their ids. API mode, the default, sends each command through the running API; local mode, `--mode local`, loads the ontology in-process.

## Taxonomies

```bash
./ai taxonomy --byod --count
./ai taxonomy nist-ai-rmf --count
./ai taxonomy --hasDocumentation NIST.AI.600-1 --count
```

## Risks

```bash
./ai risk --byod --count
./ai risk --isDefinedByTaxonomy nist-ai-rmf --count
./ai risk ai-and-coffee --byod --count
./ai risk --isPartOf granite-guardian-harm-group --count
./ai risk --risk_type inference --count
./ai risk --descriptor 'specific to generative AI' --count
./ai risk --phase training-tuning --count
```

### Risks related to Risk

```bash
./ai risk atlas-toxic-output --related_ids --count
./ai risk atlas-toxic-output --related --count
./ai risk atlas-toxic-output --related --isDefinedByTaxonomy nist-ai-rmf --count
```

## Risk Groups

```bash
./ai group --byod --count
./ai group --type CapabilityGroup --count
./ai group --isDefinedByTaxonomy ai-risk-taxonomy --count
./ai group ai-risk-taxonomy-deception --byod --count
```

## Obligations

```bash
./ai obligation --byod --count
./ai obligation --isDefinedByTaxonomy aiuc1 --count
./ai obligation --hasEvidenceCategory TECHNICAL_IMPLEMENTATION --count
./ai obligation --hasTypicalLocation 'Engineering Practice' --count
./ai obligation --hasTypicalLocation 'Engineering Tooling' --count
./ai obligation aiuc1-ctrl-b002-1 --count
```

## Recommendations

```bash
./ai recommendation --byod --count
./ai recommendation --hasEvidenceCategory LEGAL_POLICIES --count
./ai recommendation --hasEvidenceCategory OPERATIONAL_PRACTICES --count
./ai recommendation --hasTypicalLocation 'Internal policies' --count
```

## Principles

```bash
./ai principle --byod --count
./ai principle --isDefinedByTaxonomy aiuc1 --count
./ai principle --hasDocumentation AIUC-1-Jan-2026 --count
./ai principle principle-un-do-no-harm --count
```

## AI Models

```bash
./ai model --byod --count
./ai model --isPartOf shieldgemma --count
./ai model --hasRiskControl gg-groundedness-detection --count
./ai model --isProvidedBy google --count
./ai model --hasDocumentation granite-guardian-paper --count
./ai model --hasLicense gemma-terms-of-use --count
./ai model --performsTask code-generation --count
./ai model --hasInputModality modality-text --count
./ai model --hasOutputModality modality-text --count
```

## AI Tasks

```bash
./ai task --byod --count
./ai task table-question-answering --count
./ai task --isDefinedByTaxonomy hf-ml-tasks --count
./ai task --isPartOf hf-ml-tasks-group-multimodal --count
./ai task --requiresCapability ibm-cap-contextual-understanding --count
```

## Evaluations

```bash
./ai evaluation --byod --count
./ai evaluation --hasDocumentation arxiv.org/2310.12941 --count
./ai evaluation ai_eval_PopQA --count
./ai evaluation --hasDataset truthfulqa/truthful_qa --count
./ai evaluation --hasTasks text-generation --count
./ai evaluation --hasLicense license-cc-by-4.0 --count
```

### Evaluations for Risks

```bash
./ai evaluation --hasRelatedRisk atlas-hallucination --count
./ai evaluation --related --hasRelatedRisk mit-ai-causal-risk-timing-post-deployment --count
```

## Datasets

```bash
./ai dataset --byod --count
./ai dataset CybersecurityBenchmarks_datasets_frr --count
./ai dataset --hasLicense license-apache-2.0 --count
./ai dataset --hasDocumentation repo_nyu-mll_BBQ --count
./ai dataset --provider bigcode --count
```

## Adapters

```bash
./ai adapter --byod --count
./ai adapter ibm-factuality-adapter-granite-3.2-5b-harm-correction --count
./ai adapter --hasDocumentation granite-guardian-paper --count
./ai adapter --hasAdapterType LORA --count
./ai adapter --implementsCapability ibm-cap-contextual-understanding --count
./ai adapter --adaptsModel granite-guardian-3.3-8b-instruct --count
./ai adapter --hasLicense license-apache-2.0 --count
```

### Adapting to Risk

```bash
./ai adapter --hasRelatedRisk granite-relevance --count
./ai adapter --hasRelatedRisk granite-relevance --related --count
```

## LLMIntrinsics

```bash
./ai intrinsic --byod --count
./ai intrinsic --hasDocumentation arxiv.org/2504.11704 --count
./ai intrinsic ibm-factuality-intrinsic-jailbreak --count
./ai intrinsic --hasAdapter ibm-factuality-adapter-granite-3.3-8b-instruct-lora-citation-generation --count
./ai intrinsic --isDefinedByVocabulary ibm-factuality --count
```

### LLMIntrinsics for Risks

```bash
./ai intrinsic --hasRelatedRisk nist-confabulation --count
./ai intrinsic --related --hasRelatedRisk granite-answer-relevance --count
```

## Actions

```bash
./ai action --byod --count
./ai action --isDefinedByTaxonomy nist-ai-rmf --count
./ai action --byod --isDefinedByTaxonomy acme-ai-taxonomy --count
./ai action acme-action-coffee-001 --byod --count
./ai action --hasAiActorTask 'Human Factors' --count
```

### Actions for a Risk

```bash
./ai action --hasRelatedRisk nist-human-ai-configuration --count
./ai action --related_ids --hasRelatedRisk atlas-toxic-output --count
```

## Controls

```bash
./ai control --byod --count
./ai control --isDefinedByTaxonomy shieldgemma-taxonomy --count
./ai control gg-function-call-detection --count
```

### Controls for Risk

```bash
./ai control --detectsRiskConcept shieldgemma-dangerous-content --count
./ai control --hasRelatedRisk shieldgemma-hate-speech --count
./ai control --related --hasRelatedRisk atlas-toxic-output --count
```

## Incidents

```bash
./ai incident --byod --count
./ai incident --isDefinedByTaxonomy ibm-risk-atlas --count
./ai incident ibm-risk-atlas-ri-fake-legal-cases --count
```

### Incidents for Risks

```bash
./ai incident --hasRelatedRisk atlas-dangerous-use --count
./ai incident --refersToRisk atlas-evasion-attack --count
./ai incident --hasRelatedRisk atlas-dangerous-use --related --count
```

## Documents

```bash
./ai document --byod --count
./ai document repo_stanford_air_bench_2024 --count
./ai document --hasLicense license-cc-by-4.0 --count
```

## BenchmarkMetaCards

```bash
./ai benchmarkcard --count
```

## LLM Question Policies

```bash
./ai questionpolicy --byod --count
```

## Stakeholders

```bash
./ai stakeholder --byod --count
./ai stakeholder --isDefinedByTaxonomy csiro-responsible-ai-patterns --count
./ai stakeholder csiro-stakeholder-ai-technology-producers --count
./ai stakeholder --isPartOf csiro-stakeholder-group-organization-level --count
```

## Organizations

```bash
./ai organization --byod --count
./ai organization --grants_license license-cc-by-4.0 --count
```

## Export cypher queries (Neo4J integration)

```bash
./ai graph cypher --export --byod --count
```

## Export full Knowledge Graph

```bash
./ai graph --export --byod --count
```

The complete list of tested commands, with the count each is expected to return, is in [lib/test/test_cli_examples.py](../lib/test/test_cli_examples.py). The two export commands write into `graph/`. The Cypher one reads the packaged ontology only, so `--byod` does not change its output (see [Status and caveats](status.md)).
