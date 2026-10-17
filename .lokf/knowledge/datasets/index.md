# Datasets

Generated graph artifacts:

* [Knowledge-graph export (YAML + Cypher)](knowledge-graph-export.md) - Export of the AI risk knowledge graph - as ontology YAML (upstream ai-atlas-nexus data plus BYOD files) and as Cypher for Neo4j import (packaged data only).
* [NIST AI RMF crosswalks](nist-ai-rmf-crosswalks.md) - CSV crosswalks mapping NIST AI RMF risks to the FINOS AIGF, the IBM Risk Atlas, and a demo institutional (acme) risk taxonomy.

BYOD framework encodings (`byo/data/*.yaml`, built from the FINOS AIGF repository):

* [FINOS AI Governance Framework dataset](finos-aigf.md) - Risk register, mitigation catalogue and use-case library of the FINOS AI Governance Framework, encoded as ai-atlas-nexus knowledge_graph YAML.
* [EU AI Act requirements dataset](eu-ai-act.md) - Regulation (EU) 2024/1689 (EU Artificial Intelligence Act) encoded as a taxonomy with one requirement row per article.
* [FFIEC IT Handbook dataset](ffiec-it-handbook.md) - FFIEC Information Technology Examination Handbook encoded as a taxonomy with group rows per booklet and documentation rows per section.
* [ISO/IEC 42001 controls dataset](iso-42001.md) - ISO/IEC 42001 (AI management systems) Annex A controls encoded as a risk-control-group taxonomy.
* [NIST AI 600-1 GenAI profile dataset](nist-ai-600-1.md) - NIST AI 600-1 (Generative AI Profile of the AI Risk Management Framework) encoded as a risk taxonomy.
* [NIST SP 800-53 r5 controls dataset](nist-sp-800-53-r5.md) - NIST Special Publication 800-53 revision 5 security and privacy controls encoded as a risk-control-group taxonomy.
* [OWASP Top 10 for LLM Applications dataset](owasp-llm-top-10.md) - OWASP Top 10 for Large Language Model Applications encoded as a risk taxonomy.
* [OWASP ML Security Top 10 dataset](owasp-ml-top-10.md) - OWASP Machine Learning Security Top 10 encoded as a risk taxonomy.
* [SR 11-7 model risk management dataset](sr-11-7.md) - Federal Reserve SR 11-7 supervisory guidance on model risk management encoded as a risk taxonomy.
* [DuckDB record store](record-store.md) - The packaged and bring-your-own records loaded through linkml-store into DuckDB, one collection per concrete class, which the API's class listings read once built, with a trigram search index and YAML dumps.
