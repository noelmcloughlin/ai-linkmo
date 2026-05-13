# OSFF London 2026 - Presentation Outline

**Session:** From Open Data to Operations: Building AI Governance Infrastructure  
**Duration:** 30 minutes (20 min presentation + 7 min Q&A)  
**Format:** Live demo with slides

---

## Slide Structure

### Opening (3 minutes)

#### Slide 1: Title

- From Open Data to Operations: Building AI Governance Infrastructure
- Your name, organization
- OSFF London 2026

#### Slide 2: The Problem - Business Context

- Financial institutions have aggressive AI value targets
- Governance requirements create bottlenecks
- Without operational infrastructure → manual, expensive, doesn't scale
- The gap: frameworks exist, but how do you BUILD infrastructure?

#### Slide 3: What Exists Today

- Open governance data: FINOS AI Governance Framework, NIST AI RMF, Trustworthy AI taxonomies
- Expert-curated risks, mitigations, mappings
- Challenge: How to operationalize this across hundreds of AI systems?

---

### Solution Overview (5 minutes)

#### Slide 4: Reference Implementation - Four Access Patterns

Diagram showing:

```ascii
┌────────────────────────────────────┐
│  Governance Data Sources           │
│  • FINOS AI Governance Framework   │
│  • Trustworthy AI taxonomies       │
│  • Your institutional data         │
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│  AI-LinkMO Infrastructure Layer    │
│  • CLI → Automation & Pipelines    │
│  • REST API → Integration          │
│  • Web UI → Exploration            │
│  • Graph DB → Relationship Analysis│
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│  Your Operational Systems          │
│  • GRC tools                       │
│  • MLOps platforms                 │
│  • CI/CD pipelines                 │
└────────────────────────────────────┘
```

#### Slide 5: LinkMO Architecture

- Linked Data Model Operate
- Influenced by LinkML patterns from highly-regulated bioscience communities
- Cross-sector collaboration: Financial services supports health research technology
- CSR benefit: Contributing to communities advancing human medicine
- DevSecOps-ready, extensible patterns

---

### Live Demo (10 minutes)

#### Slide 6: Demo Environment Setup

- Local deployment (no internet required)
- All four access patterns operational
- Real governance data from FINOS AIGF

#### Demo Flow

**1. CLI - Automation Pattern** (2 min)

Show these commands:

```bash
# Governance team: Check risk count from taxonomy
./ai risk --isDefinedByTaxonomy nist-ai-rmf --count

# Operations: Get related items for specific risk
./ai risk atlas-toxic-output --related --count
# Exit code 0 if acceptable, non-zero if threshold exceeded

# DevSecOps: Explore risk relationships
./ai risk atlas-toxic-output --related

# Risk team: Look up realized risk (actual incident found)
./ai incident chatgpt-samsung-leak
# Real incident: Samsung leak via ChatGPT → shows related risks

# KG Traversal: Incident → Risks → Controls (Governance Coverage)
./ai incident chatgpt-samsung-leak --related  # Get related risks
./ai control --hasRelatedRisk atlas-toxic-output --count  # Find controls for specific risk
# Shows: From real incident, trace to risks, then verify control coverage
```

GitHub Actions example with model matrix:

```yaml
    - name: AI Governance Check - Model Risk Validation
      strategy:
        matrix:
          model: [granite-guardian-3.3-8b-instruct, shieldgemma-9b]
      run: |
        # Check related items count for each model
        RELATED_COUNT=$(./ai model ${{ matrix.model }} --related --count)
        echo "Model ${{ matrix.model }}: $RELATED_COUNT related items"
        if [ $RELATED_COUNT -lt 5 ]; then
          echo "⚠️  Low coverage - governance review needed"
          exit 1
        fi
    
    - name: AI Governance Check - Taxonomy Risk Count
      run: |
        RISK_COUNT=$(./ai risk --isDefinedByTaxonomy nist-ai-rmf --count)
        if [ $RISK_COUNT -gt 50 ]; then
          echo "High risk count - review required"
          exit 1
        fi
    
    - name: AI Governance Check - Control Coverage
      run: |
        # Verify high-risk areas have controls
        JAILBREAK_CONTROLS=$(./ai control --hasRelatedRisk atlas-jailbreaking --count)
        if [ $JAILBREAK_CONTROLS -lt 1 ]; then
          echo "❌ No controls for jailbreaking risk"
          exit 1
        fi
        echo "✅ Jailbreaking has $JAILBREAK_CONTROLS controls"
```

- Exit codes for pipeline integration
- Same pattern as security scanners (Snyk, Veracode)

**2. REST API - Integration Pattern** (2 min)

- FastAPI documentation at /docs
- Query endpoints
- Show JSON responses
- Integration with GRC tools

**3. Web UI - Exploration Pattern** (3 min)

- Browse risk categories
- Explore risk details and mitigations
- Filter and search capabilities
- User-friendly for non-technical stakeholders

**4. Graph DB - Analysis Pattern** (3 min)

- Relationship visualization
- Risk → Control → Model connections
- Regulatory crosswalks (NIST AI RMF ↔ EU AI Act ↔ FINOS AIGF)
- Evidence generation for audits

---

### Key Benefits (4 minutes)

#### Slide 7: Business Impact

- **Scale without scaling costs:** Apply governance across hundreds of AI systems
- **Reduce friction:** Bridge delivery teams and control functions
- **Stay ahead:** Consume open standards as they emerge ("Start Left" of regulations)
- **Compliance confidence:** Automated evidence generation, audit trails

#### Slide 8: Architecture Benefits

- **Extensible:** Bring Your Own Data—combine public + confidential governance
- **Proven patterns:** Inspired by LinkML from highly-regulated bioscience communities
- **DevSecOps-ready:** CLI with exit codes, API endpoints, automated gates
- **Open source:** Deploy today, adapt to your context

#### Slide 8b: DevSecOps Integration - In Action

Complete GitHub Actions workflow:

```yaml
name: AI Model Governance Check

on:
  pull_request:
    paths:
      - 'models/**'
      - 'ml_configs/**'

jobs:
  governance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup AI Governance CLI
        run: |
          pip install ai-linkmo
          
      - name: Risk Assessment - Taxonomy Coverage
        run: |
          # Check risks from governance taxonomy
          RISK_COUNT=$(./ai risk --isDefinedByTaxonomy nist-ai-rmf --count)
          echo "NIST AI RMF risks: $RISK_COUNT"
          ./ai risk --isDefinedByTaxonomy nist-ai-rmf --pretty > nist-risks.json
          
      - name: Governance Gate - Risk Threshold
        run: |
          RISK_COUNT=$(./ai risk --isDefinedByTaxonomy nist-ai-rmf --count)
          if [ "$RISK_COUNT" -gt 50 ]; then
            echo "❌ High risk count: $RISK_COUNT - Governance review required"
            exit 1
          fi
          echo "✅ Risk count acceptable: $RISK_COUNT"
      
      - name: KG Traversal - Control Coverage Validation
        run: |
          # Verify critical risks have controls (Graph traversal)
          HALLUCINATION_CONTROLS=$(./ai control --hasRelatedRisk atlas-hallucination --count)
          JAILBREAK_CONTROLS=$(./ai control --hasRelatedRisk atlas-jailbreaking --count)
          
          if [ $HALLUCINATION_CONTROLS -lt 1 ]; then
            echo "❌ No controls for hallucination risk"
            exit 1
          fi
          
          if [ $JAILBREAK_CONTROLS -lt 1 ]; then
            echo "❌ No controls for jailbreaking risk"
            exit 1
          fi
          
          echo "✅ Critical risks have controls: Hallucination($HALLUCINATION_CONTROLS), Jailbreak($JAILBREAK_CONTROLS)"
      
      - name: Model Validation Matrix
        strategy:
          matrix:
            model: [granite-guardian-3.3-8b-instruct, shieldgemma-9b]
        run: |
          # Check each model's governance coverage
          echo "Validating model: ${{ matrix.model }}"
          RELATED_COUNT=$(./ai model ${{ matrix.model }} --related --count)
          echo "Related items: $RELATED_COUNT"
          
      - name: Incident Analysis - Real Risk Validation
        run: |
          # KG Traversal: Incident → Risks → Controls
          echo "Analyzing ChatGPT Samsung leak incident..."
          ./ai incident chatgpt-samsung-leak --related > incident-risks.json
          
          # Verify we have controls for risks from real incidents
          TOXIC_CONTROLS=$(./ai control --hasRelatedRisk atlas-toxic-output --count)
          echo "Controls for incident-related risks: $TOXIC_CONTROLS"
          
      - name: Generate Compliance Report
        run: |
          ./ai risk --isDefinedByTaxonomy nist-ai-rmf --pretty > compliance-report.json
          
      - name: Comment PR with Results
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('compliance-report.json', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## AI Governance Check\n\n${report}`
            });
```

Real-world usage:

- **Pre-deployment:** Gate before production
- **Continuous monitoring:** Scheduled scans
- **Audit trail:** Automated evidence generation

#### Slide 9: Cross-Sector Collaboration & CSR

- Adopting LinkML from biomedical research communities
- Financial services benefits from health research technology
- Contributing back to communities serving human welfare
- CSR through technology choices: mutual benefit

#### Slide 9b: Operations in Action - Real Command Examples

**Governance Team - Morning Risk Review:**

```bash
# Count risks from NIST AI RMF taxonomy
./ai risk --isDefinedByTaxonomy nist-ai-rmf --count

# Get risks related to specific risk (relationship traversal)
./ai risk atlas-toxic-output --related

# Find realized risks (actual incidents)
./ai incident chatgpt-samsung-leak
# Returns: Samsung employee leak of proprietary code via ChatGPT (2023)

# KG Traversal: Get related items for an incident
./ai incident chatgpt-samsung-leak --related
# Shows related risks and context - traces from real-world incident to risk taxonomy
```

**Risk Intelligence Team - KG Analysis:**

```bash
# Multi-hop Graph Traversal: Incident → Risk → Controls
# Step 1: Find the incident
./ai incident chatgpt-samsung-leak

# Step 2: Trace to related risks  
./ai incident chatgpt-samsung-leak --related

# Step 3: For each risk, find detecting controls
./ai control --hasRelatedRisk atlas-toxic-output --count
./ai control --hasRelatedRisk atlas-jailbreaking --count
# Shows: From real incident, trace through KG to find applicable controls

# Control Coverage Gap Analysis
./ai risk --isDefinedByTaxonomy granite-guardian --count  # Total risks
./ai control --isDefinedByTaxonomy granite-guardian --count  # Available controls
# Compare: Are all risks covered by controls?

# Taxonomy Crosswalk: Compare frameworks
./ai risk --isDefinedByTaxonomy nist-ai-rmf --count  # 12 NIST risks
./ai risk --isDefinedByTaxonomy ibm-risk-atlas --count  # 4 IBM risks
./ai risk --isDefinedByTaxonomy ai-risk-taxonomy --count  # 127 detailed risks
# Shows: Different granularity levels across governance frameworks
```

**DevOps Engineer - Pre-Deployment Validation:**

```bash
# Validate model exists and get details
./ai model granite-guardian-3.3-8b-instruct

# Check model's related governance items (controls, risks, evaluations)
./ai model granite-guardian-3.3-8b-instruct --related --count

# Find models by provider (inventory management)
./ai model --isProvidedBy ibm --count

# Find models that implement specific controls
./ai model --hasRiskControl gg-groundedness-detection --count
# Shows: Which models have built-in hallucination detection

# Evaluation Coverage: Check if model has been tested
./ai evaluation --hasTasks text-generation --count
./ai evaluation --hasRelatedRisk atlas-hallucination --count
# Shows: Testing coverage for specific capabilities and risks
```

**Compliance Officer - Audit Preparation:**

```bash
# Generate NIST AI RMF risk list
./ai risk --isDefinedByTaxonomy nist-ai-rmf --pretty > nist-risks.json

# Get controls for specific taxonomy
./ai control --isDefinedByTaxonomy aiuc1 --count

# AIUC-1 Compliance: Check obligations and recommendations
./ai obligation --isDefinedByTaxonomy aiuc1 --count  # 79 obligations
./ai recommendation --isDefinedByTaxonomy aiuc1 --count  # Check recommendations
# Shows: Complete AIUC-1 framework coverage

# Regulatory Crosswalk: Multi-taxonomy analysis
./ai taxonomy --count  # See all available frameworks
./ai risk --isDefinedByTaxonomy nist-ai-rmf --count  # NIST coverage
./ai obligation --hasEvidenceCategory TECHNICAL_IMPLEMENTATION --count  # Technical controls
./ai obligation --hasEvidenceCategory LEGAL_POLICIES --count  # Policy requirements
# Shows: Cross-framework compliance mapping
```

**Platform Team - Pipeline Integration:**

```bash
# Jenkins/GitLab CI pipeline - check risk count
RISK_COUNT=$(./ai risk --isDefinedByTaxonomy nist-ai-rmf --count)
if [ $RISK_COUNT -gt 50 ]; then exit 1; fi
# Returns exit code 1 if risk count exceeds threshold
```

---

### Takeaways (3 minutes)

#### Slide 10: What You Get

- Complete open-source reference architecture
- Working code: CLI, API, Web UI, Graph DB
- Architecture patterns and design decisions
- Deployment documentation
- Extensibility for your institutional needs

#### Slide 11: Call to Action

- GitHub repository: [URL]
- Deploy and adapt immediately
- Contribute governance data back to community
- "Start Left" approach: consume standards as they emerge
- Join the collaboration

#### Slide 12: Key Takeaways

1. Open governance data exists (FINOS AIGF) → Reference implementation shows HOW to build infrastructure
2. Four access patterns enable automation, integration, exploration, and analysis
3. DevSecOps-ready architecture from regulated industries
4. Cross-sector collaboration: financial services + bioscience communities
5. Working code available today—not theory, not future plans

---

### Q&A (7 minutes)

#### Slide 13: Questions?

- Your contact info
- GitHub repository link
- LinkedIn/professional contact

---

## Key Talking Points to Memorize

### Opening Hook

"Open governance data exists—FINOS AIGF, NIST AI RMF, Trustworthy AI taxonomies. The question is: how do you actually BUILD operational infrastructure that makes this work across hundreds of AI systems?"

### Core Message

"This is a reference implementation showing how to operationalize governance frameworks. Not theory—working code with four access patterns you can deploy today."

### DevSecOps Angle

"CLI with exit codes, API endpoints, automated gates—the same pattern you use for security scanners, now applied to AI governance. Look at this GitHub Actions workflow: before your model deploys to production, it automatically checks the risk profile. If risk count exceeds your threshold, the pipeline fails—just like Snyk or Veracode. Governance becomes part of your CI/CD, not a separate manual process. The governance team runs morning reports, DevOps gates deployments, compliance generates audit reports—all from the same CLI and API."

### CSR Angle

"LinkMO adopts patterns from LinkML—a data modeling standard from biomedical research communities working to improve human medicine. By using LinkML-compatible architecture, financial services benefits from proven technology while supporting communities with a social mission."

### Closing

"Everything is open source. Deploy it, adapt it, contribute back. Let's build this together."

---

## Demo Preparation Checklist

### Before Presentation

- [ ] Virtual environment activated
- [ ] All services running (API, UI, Graph DB)
- [ ] Terminal with clean prompt ready
- [ ] Browser tabs open: FastAPI docs, Web UI, Neo4J
- [ ] Sample queries tested
- [ ] Backup slides/video ready if demo fails

### Technical Setup

- [ ] Port 8000: API server
- [ ] Port 5173: Web UI
- [ ] Port 7474: Neo4J browser
- [ ] Terminal font size readable from distance
- [ ] High contrast theme for visibility

### Content Verification

- [ ] Latest governance data loaded
- [ ] Example queries produce expected results
- [ ] Graph visualizations render correctly
- [ ] All four access patterns functional
- [ ] DevSecOps CLI examples tested and working
- [ ] GitHub Actions workflow slide visible and readable
- [ ] Exit code demonstrations work (--count commands)
- [ ] All persona-based commands (governance, DevOps, compliance) ready to show
