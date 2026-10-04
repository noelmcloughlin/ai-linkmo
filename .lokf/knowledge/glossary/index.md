# Glossary

The domain vocabulary of AI-LinkMO, as defined in `docs/key-concepts.md` and carried by the [AI Risk Ontology](../references/ai-risk-ontology.md):

* [Taxonomy](taxonomy.md) - A framework's catalogue of risks/controls; the unit each BYOD data file and each `--isDefinedByTaxonomy` query is scoped to.
* [Risk](risk.md) - A named, identified harm carrying a persistent identifier, defined by one taxonomy and mappable to equivalents in others.
* [Control / Action](control-action.md) - The mitigation side of the model - what an organisation does or deploys against a risk; served by the /control and /action endpoints.
* [Obligation](obligation.md) - A framework-imposed requirement together with the evidence categories that demonstrate compliance; served by the /obligation endpoint.
* [Crosswalk](crosswalk.md) - A generated mapping of equivalent concepts across two taxonomies, replacing hand-built spreadsheet crosswalks.
* [Incident](incident.md) - A documented occurrence of a risk, carrying its source and linked back to the risks it demonstrates; served by the /incident endpoint.
* [Evaluation](evaluation.md) - A benchmark or test measuring a risk or a capability, linked to its datasets and tasks; served by the /evaluation endpoint.
* [Bring Your Own Data](byod.md) - The pattern of encoding institutional governance data in the AI Risk Ontology schema so it is served alongside the public frameworks.
