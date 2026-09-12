# CLI examples: every entity type, one command away

Every command below is also a test case in [lib/test/test_cli_examples.py](../lib/test/test_cli_examples.py), run in both API mode and local mode, so the list stays honest. `--count` prints the number of matches; drop it to see the records. The CLI is generated from [lib/api/openapi.yaml](../lib/api/openapi.yaml), so `./ai <scope> -h` always shows the current flags.

| Examples from [test_cli_examples](../lib/test/test_cli_examples.py) |
| :------------------------------- |
| Taxonomies |
| `./ai taxonomy --byod --count` |
| `./ai taxonomy nist-ai-rmf --count` |
| `./ai taxonomy --hasDocumentation NIST.AI.600-1 --count` |
| Risks |
| `./ai risk --byod --count` |
| `./ai risk --isDefinedByTaxonomy nist-ai-rmf --count` |
| `./ai risk ai-and-coffee --byod --count` |
| `./ai risk --isPartOf granite-guardian-harm-group --count` |
| `./ai risk --risk_type inference --count` |
| `./ai risk --descriptor 'specific to generative AI' --count` |
| `./ai risk --phase training-tuning --count` |
| > Risks related to Risk |
| `./ai risk atlas-toxic-output --related_ids --count` |
| `./ai risk atlas-toxic-output --related --count` |
| `./ai risk atlas-toxic-output --related --isDefinedByTaxonomy nist-ai-rmf --count` |
| Risk Groups |
| `./ai group --byod --count` |
| `./ai group --type CapabilityGroup --count` |
| `./ai group --isDefinedByTaxonomy ai-risk-taxonomy --count` |
| `./ai group ai-risk-taxonomy-deception --byod --count` |
| Obligations |
| `./ai obligation --byod --count` |
| `./ai obligation --isDefinedByTaxonomy aiuc1 --count` |
| `./ai obligation --hasEvidenceCategory TECHNICAL_IMPLEMENTATION --count` |
| `./ai obligation --hasTypicalLocation 'Engineering Practice' --count` |
| `./ai obligation --hasTypicalLocation 'Engineering Tooling' --count` |
| `./ai obligation aiuc1-ctrl-b002-1 --count` |
| Recommendations |
| `./ai recommendation --byod --count` |
| `./ai recommendation --hasEvidenceCategory LEGAL_POLICIES --count` |
| `./ai recommendation --hasEvidenceCategory OPERATIONAL_PRACTICES --count` |
| `./ai recommendation --hasTypicalLocation 'Internal policies' --count` |
| Principles |
| `./ai principle --byod --count` |
| `./ai principle --isDefinedByTaxonomy aiuc1 --count` |
| `./ai principle --hasDocumentation AIUC-1-Jan-2026 --count` |
| `./ai principle principle-un-do-no-harm --count` |
| AI Models |
| `./ai model --byod --count` |
| `./ai model --isPartOf shieldgemma --count` |
| `./ai model --hasRiskControl gg-groundedness-detection --count` |
| `./ai model --isProvidedBy google --count` |
| `./ai model --hasDocumentation granite-guardian-paper --count` |
| `./ai model --hasLicense gemma-terms-of-use --count` |
| `./ai model --performsTask code-generation --count` |
| `./ai model --hasInputModality modality-text --count` |
| `./ai model --hasOutputModality modality-text --count` |
| AI Tasks |
| `./ai task --byod --count` |
| `./ai task table-question-answering --count` |
| `./ai task --isDefinedByTaxonomy hf-ml-tasks --count` |
| `./ai task --isPartOf hf-ml-tasks-group-multimodal --count` |
| `./ai task --requiresCapability ibm-cap-contextual-understanding --count` |
| Evaluations |
| `./ai evaluation --byod --count` |
| `./ai evaluation --hasDocumentation arxiv.org/2310.12941 --count` |
| `./ai evaluation ai_eval_PopQA --count` |
| `./ai evaluation --hasDataset truthfulqa/truthful_qa --count` |
| `./ai evaluation --hasTasks text-generation --count` |
| `./ai evaluation --hasLicense license-cc-by-4.0 --count` |
| > Evaluations for Risks |
| `./ai evaluation --hasRelatedRisk atlas-hallucination --count` |
| `./ai evaluation --related --hasRelatedRisk mit-ai-causal-risk-timing-post-deployment --count` |
| Datasets |
| `./ai dataset --byod --count` |
| `./ai dataset CybersecurityBenchmarks_datasets_frr --count` |
| `./ai dataset --hasLicense license-apache-2.0 --count` |
| `./ai dataset --hasDocumentation repo_nyu-mll_BBQ --count` |
| `./ai dataset --provider bigcode --count` |
| Adapters |
| `./ai adapter --byod --count` |
| `./ai adapter ibm-factuality-adapter-granite-3.2-5b-harm-correction --count` |
| `./ai adapter --hasDocumentation granite-guardian-paper --count` |
| `./ai adapter --hasAdapterType LORA --count` |
| `./ai adapter --implementsCapability ibm-cap-contextual-understanding --count` |
| `./ai adapter --adaptsModel granite-guardian-3.3-8b-instruct --count` |
| `./ai adapter --hasLicense license-apache-2.0 --count` |
| > Adapting to Risk |
| `./ai adapter --hasRelatedRisk granite-relevance --count` |
| `./ai adapter --hasRelatedRisk granite-relevance --related --count` |
| LLMIntrinsics |
| `./ai intrinsic --byod --count` |
| `./ai intrinsic --hasDocumentation arxiv.org/2504.11704 --count` |
| `./ai intrinsic ibm-factuality-intrinsic-jailbreak --count` |
| `./ai intrinsic --hasAdapter ibm-factuality-adapter-granite-3.3-8b-instruct-lora-citation-generation --count` |
| `./ai intrinsic --isDefinedByVocabulary ibm-factuality --count` |
| > LLMIntrinsics for Risks |
| `./ai intrinsic --hasRelatedRisk nist-confabulation --count` |
| `./ai intrinsic --related --hasRelatedRisk granite-answer-relevance --count` |
| Actions |
| `./ai action --byod --count` |
| `./ai action --isDefinedByTaxonomy nist-ai-rmf --count` |
| `./ai action --byod --isDefinedByTaxonomy acme-ai-taxonomy --count` |
| `./ai action acme-action-coffee-001 --byod --count` |
| `./ai action --hasAiActorTask 'Human Factors' --count` |
| > Actions for a Risk |
| `./ai action --hasRelatedRisk nist-human-ai-configuration --count` |
| `./ai action --related_ids --hasRelatedRisk atlas-toxic-output --count` |
| Controls |
| `./ai control --byod --count` |
| `./ai control --isDefinedByTaxonomy shieldgemma-taxonomy --count` |
| `./ai control gg-function-call-detection --count` |
| > Controls for Risk |
| `./ai control --detectsRiskConcept shieldgemma-dangerous-content --count` |
| `./ai control --hasRelatedRisk shieldgemma-hate-speech --count` |
| `./ai control --related --hasRelatedRisk atlas-toxic-output --count` |
| Incidents |
| `./ai incident --byod --count` |
| `./ai incident --isDefinedByTaxonomy ibm-risk-atlas --count` |
| `./ai incident ibm-risk-atlas-ri-fake-legal-cases --count` |
| > Incidents for Risks |
| `./ai incident --hasRelatedRisk atlas-dangerous-use --count` |
| `./ai incident --refersToRisk atlas-evasion-attack --count` |
| `./ai incident --hasRelatedRisk atlas-dangerous-use --related --count` |
| Documents |
| `./ai document --byod --count` |
| `./ai document repo_stanford_air_bench_2024 --count` |
| `./ai document --hasLicense license-cc-by-4.0 --count` |
| BenchmarkMetaCards |
| `./ai benchmarkcard --count` |
| LLM Question Policies |
| `./ai questionpolicy --byod --count` |
| Stakeholders |
| `./ai stakeholder --byod --count` |
| `./ai stakeholder --isDefinedByTaxonomy csiro-responsible-ai-patterns --count` |
| `./ai stakeholder csiro-stakeholder-ai-technology-producers --count` |
| `./ai stakeholder --isPartOf csiro-stakeholder-group-organization-level --count` |
| Organizations |
| `./ai organization --byod --count` |
| `./ai organization --grants_license license-cc-by-4.0 --count` |
| |
| Export cypher queries (Neo4J integration) |
| `./ai graph cypher --export --byod --count` |
| Export full Knowledge Graph |
| `./ai graph --export --byod --count` |

And so on. The two export commands write into `graph/`; the Cypher one reads the packaged ontology only, so `--byod` does not change its output (see the README's [Status and caveats](../README.md#status-and-caveats)).
