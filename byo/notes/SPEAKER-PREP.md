# OSFF London 2026 - Speaker Prep

Quick reference for speaker preparation and Q&A responses.

---

## 30-Second Elevator Pitch

"This is a reference implementation showing how to operationalize AI governance frameworks like FINOS AIGF. Instead of everyone building infrastructure from scratch, we provide working code: CLI, API, Web UI, Graph DB—four access patterns to consume open governance data. DevSecOps-ready architecture inspired by patterns from regulated bioscience communities. Deploy today, adapt to your context."

---

## Core Messages

1. **Gap we're filling:** Open governance data exists (FINOS AIGF), but infrastructure showing HOW to operationalize it doesn't
2. **Four access patterns:** CLI for automation, API for integration, UI for exploration, Graph DB for analysis
3. **DevSecOps-ready:** Proven patterns from highly-regulated industries
4. **Cross-sector collaboration:** Financial services benefits from bioscience technology, supports communities advancing human health
5. **Working code:** Not theory or future plans—deploy today

---

## Key Statistics to Mention

- **Multiple governance sources:** FINOS AIGF, NIST AI RMF, Trustworthy AI taxonomies
- **Four operational patterns:** CLI, API, UI, Graph DB for different use cases
- **DevSecOps integration:** Exit codes, API endpoints, automated gates like security scanners
- **Open source:** Complete reference architecture available today

---

## Demo Flow (10 minutes)

### 1. CLI - Automation (2 min)

*Show:*

```bash
# Query risks
./ai risk --count

# Find mitigations for specific risk
./ai risk atlas-toxic-output --related

# Pipeline-ready: exit codes for CI/CD
./ai model --isProvidedBy ibm --count
```

*Say:* "Just like security scanners in your pipelines—exit codes, automation-ready, DevSecOps integration."

### 2. REST API - Integration (2 min)

*Show:* FastAPI docs at localhost:8000/docs

- Browse endpoints
- Execute sample query
- Show JSON response

*Say:* "Standard REST API with OpenAPI docs. Integrate with any GRC tool, dashboard, or internal system."

### 3. Web UI - Exploration (3 min)

*Show:* Web app at localhost:5173

- Browse risk categories
- Click through risk details
- Show mitigation recommendations
- Demonstrate filtering

*Say:* "User-friendly interface for governance teams, non-technical stakeholders. Explore relationships, understand risks, find controls."

### 4. Graph DB - Analysis (3 min)

*Show:* Neo4J browser at localhost:7474

- Visualize risk → control → model relationships
- Show regulatory crosswalks (NIST ↔ EU AI Act ↔ FINOS AIGF)
- Demonstrate path finding

*Say:* "Graph database reveals relationships. Compliance questions like 'which controls address this EU AI Act obligation?' become queries, not manual searches."

---

## Q&A - Prepared Responses

### "How is this different from FINOS AIGF?"

"FINOS AIGF provides the governance data—the risks, mitigations, expert knowledge. This is the infrastructure layer showing HOW to operationalize that data through CLI, API, Web UI, and Graph DB. Complementary, not competing."

### "Why not just use existing GRC tools?"

"GRC tools manage your organization's governance. This provides the shared knowledge layer about AI-specific risks, models, controls, regulatory mappings. Think of it as the 'Wikipedia' layer that informs your GRC tool about the AI governance landscape."

### "How does this integrate with DevSecOps pipelines?"

"Just like security scanners. CLI returns exit codes—zero for pass, non-zero for issues. Run it in GitHub Actions, Jenkins, GitLab CI. Set thresholds: if high-risk count exceeds limit, fail the build. Same pattern you already use."

### "What about proprietary governance data?"

"That's the BYOD—Bring Your Own Data—model. The architecture supports both public data from FINOS AIGF and your confidential institutional governance. They coexist in your local deployment."

### "What's the LinkMO / bioscience connection?"

"LinkMO adopts patterns from LinkML—a data modeling standard from biomedical research communities like NIH genomics and clinical data integration. Proven in highly-regulated environments. By using LinkML-compatible architecture for financial services, we benefit from proven technology while supporting communities focused on human health research. Cross-sector collaboration with CSR benefits."

### "Is the data up to date?"

"Community contribution model, like open source software. When new foundation models launch with new risks, the community documents them. When regulations change, taxonomies update. Better than every institution duplicating that effort independently."

### "Can I see the code?"

"Yes! Everything is open source on GitHub. Apache 2.0 / MIT licenses. Complete reference architecture: CLI, API, Web UI, Graph DB. Deployment documentation included. Clone it, deploy it, adapt it."

### "What's required to deploy this?"

"Python 3.11+, Docker for Neo4J, standard web stack. Full installation instructions in README. Runs locally or in your cloud. No external dependencies required—can run completely offline."

---

## Handling Tough Questions

### If demo fails

"Let me show you the backup video / slides demonstrating the same functionality. [Have backup prepared.] The complete working code is in the GitHub repo—you can deploy it yourself to see it in action."

### If asked about production readiness

"This is a reference implementation—production-ready patterns but you'll want to customize for your environment. Security, authentication, data governance policies—those are institutional decisions. The architecture patterns are proven; the implementation details are yours to own."

### If asked about maintenance

"Community-driven model. As regulations evolve, as new models launch, the community updates governance data. You consume those updates, just like you update security scanner rules. Governance knowledge stays current through shared maintenance."

---

## Positioning Notes

### You are presenting

Reference implementation / infrastructure layer / presentation layer

### You are NOT presenting

Core FINOS AI Governance Framework, AI Atlas Nexus core ontology

### Your contribution

Showing HOW to build operational systems that consume open governance data

### Key differentiation

Working code, DevSecOps patterns, four access modes, deploy-ready architecture

### CSR angle

Cross-sector collaboration with bioscience communities, supporting human health research technology

---

## Opening & Closing

### Opening (after intro slide)

"By show of hands, how many of you are familiar with FINOS AIGF? [pause] Good. Now, how many have built operational infrastructure to consume that data in production? [expect fewer hands] That gap is exactly what we're solving today."

### Closing (before Q&A)

"Three takeaways: First, open governance data exists—FINOS AIGF provides expert knowledge. Second, this reference implementation shows HOW to operationalize it with working code. Third, everything is open source and available today. Deploy it, adapt it, contribute back. Let's build this together. Questions?"

---

## Speaker Bio (100 words - if needed)

[TEMPLATE - Customize with your details]

[Your Name] is [role] at [organization], specializing in infrastructure automation and AI governance for financial services. Influenced by the LinkML community—focused on biomedical research and improving human medicine—[he/she/they] conceived and built a reference implementation demonstrating how to operationalize AI governance frameworks through CLI, API, Web UI, and Graph DB architecture. Using LinkML-compatible patterns supports cross-sector CSR collaboration between financial services and healthcare research communities. With experience in enterprise architecture and DevSecOps, [Name] focuses on practical, automation-first approaches to compliance in regulated industries.
