"""Test CLI commands from README examples.

This test suite validates all CLI commands documented in README.md,
ensuring they work correctly in both API and local modes. When data
changes ("bring your own data", upgraded 'ai_atlas_nexus' package),
you need to update the test suite accordingly.
"""

import pytest


# Test cases extracted from README.md
# Format: (command_args, expected_count_min, expected_count_max, byod_required)
CLI_TEST_CASES = [
    # Taxonomies
    (["taxonomy", "--count"], 12, 12, False),
    (["taxonomy", "--byod", "--count"], 14, None, True),
    (["taxonomy", "nist-ai-rmf"], 1, 1, False),
    (["taxonomy", "--hasDocumentation", "NIST.AI.600-1", "--count"], 1, 1, False),
    
    # Risks
    (["risk", "--count"], 546, 546, False),
    (["risk", "--byod", "--count"], 549, None, True),
    (["risk", "--isDefinedByTaxonomy", "nist-ai-rmf", "--count"], 12, 12, False),
    (["risk", "--isPartOf", "granite-guardian-harm-group", "--count"], 7, 7, False),
    (["risk", "--risk_type", "inference", "--count"], 18, 18, False),
    (["risk", "--descriptor", "specific to generative AI", "--count"], 31, 31, False),
    (["risk", "--phase", "training-tuning", "--count"], 0, 0, False),
    
    # Risks related to Risk
    (["risk", "atlas-toxic-output", "--related_ids", "--count"], 13, 13, False),
    (["risk", "atlas-toxic-output", "--related", "--count"], 13, 13, False),
    (["risk", "atlas-toxic-output", "--related", "--isDefinedByTaxonomy", "nist-ai-rmf", "--count"], 2, 2, False),
    
    # Risk Groups
    (["group", "--count"], 153, 153, False),
    (["group", "--type", "CapabilityGroup", "--count"], 8, 8, False),
    (["group", "--isDefinedByTaxonomy", "ai-risk-taxonomy", "--count"], 59, 59, False),
    (["group", "ai-risk-taxonomy-deception"], 1, 1, False),
    
    # Obligations
    (["obligation", "--count"], 79, 79, False),
    (["obligation", "--isDefinedByTaxonomy", "aiuc1", "--count"], 79, 79, False),
    (["obligation", "--hasEvidenceCategory", "TECHNICAL_IMPLEMENTATION", "--count"], 48, 48, False),
    (["obligation", "--hasTypicalLocation", "Engineering Practice", "--count"], 6, 6, False),
    (["obligation", "--hasTypicalLocation", "Engineering Tooling", "--count"], 9, 9, False),
    (["obligation", "aiuc1-ctrl-b002-1"], 1, 1, False),
    
    # Recommendations
    (["recommendation", "--count"], 50, 50, False),
    (["recommendation", "--hasEvidenceCategory", "LEGAL_POLICIES", "--count"], 3, 3, False),
    (["recommendation", "--hasEvidenceCategory", "OPERATIONAL_PRACTICES", "--count"], 15, 15, False),
    (["recommendation", "--hasTypicalLocation", "Internal policies", "--count"], 3, 3, False),
    
    # Principles
    (["principle", "--count"], 32, 32, False),
    (["principle", "--isDefinedByTaxonomy", "aiuc1", "--count"], 6, 6, False),
    (["principle", "--hasDocumentation", "AIUC-1-Jan-2026", "--count"], 6, 6, False),
    (["principle", "principle-un-do-no-harm"], 1, 1, False),
    
    # AI Models
    (["model", "--count"], 11, 11, False),
    (["model", "--isPartOf", "shieldgemma", "--count"], 3, 3, False),
    (["model", "--hasRiskControl", "gg-groundedness-detection", "--count"], 5, 5, False),
    (["model", "--isProvidedBy", "google", "--count"], 3, 3, False),
    (["model", "--hasDocumentation", "granite-guardian-paper", "--count"], 5, 5, False),
    (["model", "--hasLicense", "gemma-terms-of-use", "--count"], 3, 3, False),
    (["model", "--performsTask", "code-generation", "--count"], 3, 3, False),
    (["model", "--hasInputModality", "modality-text", "--count"], 11, 11, False),
    (["model", "--hasOutputModality", "modality-text", "--count"], 11, 11, False),
    
    # AI Tasks
    (["task", "--count"], 52, 52, False),
    (["task", "table-question-answering"], 1, 1, False),
    (["task", "--isDefinedByTaxonomy", "hf-ml-tasks", "--count"], 47, 47, False),
    (["task", "--isPartOf", "hf-ml-tasks-group-multimodal", "--count"], 9, 9, False),
    (["task", "--requiresCapability", "ibm-cap-contextual-understanding", "--count"], 10, 10, False),
    
    # Evaluations
    (["evaluation", "--count"], 24, 25, False),
    (["evaluation", "--hasDocumentation", "arxiv.org/2310.12941", "--count"], 1, 1, False),
    (["evaluation", "ai_eval_PopQA"], 1, 1, False),
    (["evaluation", "--hasDataset", "truthfulqa/truthful_qa", "--count"], 1, 1, False),
    (["evaluation", "--hasTasks", "text-generation", "--count"], 5, 5, False),
    (["evaluation", "--hasLicense", "license-cc-by-4.0", "--count"], 3, 3, False),
    
    # Evaluations for Risks
    (["evaluation", "--hasRelatedRisk", "atlas-hallucination", "--count"], 2, 2, False),
    (["evaluation", "--related", "--hasRelatedRisk", "mit-ai-causal-risk-timing-post-deployment", "--count"], 25, 25, False),
    
    # Datasets
    (["dataset", "--count"], 26, 26, False),
    (["dataset", "CybersecurityBenchmarks_datasets_frr"], 1, 1, False),
    (["dataset", "--hasLicense", "license-apache-2.0", "--count"], 5, 5, False),
    (["dataset", "--hasDocumentation", "repo_nyu-mll_BBQ", "--count"], 1, 1, False),
    (["dataset", "--provider", "bigcode", "--count"], 1, 1, False),
    
    # Adapters
    (["adapter", "--count"], 19, 19, False),
    (["adapter", "ibm-factuality-adapter-granite-3.2-5b-harm-correction"], 1, 1, False),
    (["adapter", "--hasDocumentation", "granite-guardian-paper", "--count"], 2, 2, False),
    (["adapter", "--hasAdapterType", "LORA", "--count"], 12, 12, False),
    (["adapter", "--implementsCapability", "ibm-cap-contextual-understanding", "--count"], 5, 5, False),
    (["adapter", "--adaptsModel", "granite-guardian-3.3-8b-instruct", "--count"], 12, 12, False),
    (["adapter", "--hasLicense", "license-apache-2.0", "--count"], 3, 3, False),
    
    # Adapting to Risk
    (["adapter", "--hasRelatedRisk", "granite-relevance", "--count"], 1, 1, False),
    (["adapter", "--hasRelatedRisk", "granite-relevance", "--related", "--count"], 0, 0, False),
    
    # LLMIntrinsics
    (["intrinsic", "--count"], 9, 9, False),
    (["intrinsic", "--hasDocumentation", "arxiv.org/2504.11704", "--count"], 8, 8, False),
    (["intrinsic", "ibm-factuality-intrinsic-jailbreak"], 1, 1, False),
    (["intrinsic", "--hasAdapter", "ibm-factuality-adapter-granite-3.3-8b-instruct-lora-citation-generation", "--count"], 1, 1, False),
    (["intrinsic", "--isDefinedByVocabulary", "ibm-factuality", "--count"], 9, 9, False),
    
    # LLMIntrinsics for Risks
    (["intrinsic", "--hasRelatedRisk", "nist-confabulation", "--count"], 1, 1, False),
    (["intrinsic", "--related", "--hasRelatedRisk", "granite-answer-relevance", "--count"], 4, 4, False),
    
    # Actions
    (["action", "--count"], 254, 254, False),
    (["action", "--isDefinedByTaxonomy", "nist-ai-rmf", "--count"], 212, 212, False),
    (["action", "--hasAiActorTask", "Human Factors", "--count"], 22, 22, False),
    
    # Actions for a Risk
    (["action", "--hasRelatedRisk", "nist-human-ai-configuration", "--count"], 53, 53, False),
    (["action", "--related_ids", "--hasRelatedRisk", "atlas-toxic-output", "--count"], 47, 47, False),
    
    # Controls
    (["control", "--count"], 848, 848, False),
    (["control", "--isDefinedByTaxonomy", "shieldgemma-taxonomy", "--count"], 4, 4, False),
    (["control", "gg-function-call-detection"], 1, 1, False),
    
    # Controls for Risk
    (["control", "--detectsRiskConcept", "shieldgemma-dangerous-content", "--count"], 1, 1, False),
    (["control", "--hasRelatedRisk", "shieldgemma-hate-speech", "--count"], 1, 1, False),
    (["control", "--related", "--hasRelatedRisk", "atlas-toxic-output", "--count"], 4, 4, False),
    
    # Incidents
    (["incident", "--count"], 38, 38, False),
    (["incident", "--isDefinedByTaxonomy", "ibm-risk-atlas", "--count"], 38, 38, False),
    (["incident", "ibm-risk-atlas-ri-fake-legal-cases"], 1, 1, False),
    
    # Incidents for Risks
    (["incident", "--hasRelatedRisk", "atlas-dangerous-use", "--count"], 2, 2, False),
    (["incident", "--refersToRisk", "atlas-evasion-attack", "--count"], 1, 1, False),
    (["incident", "--hasRelatedRisk", "atlas-dangerous-use", "--related", "--count"], 0, 0, False),
    
    # Documents
    (["document", "--count"], 67, 67, False),
    (["document", "repo_stanford_air_bench_2024"], 1, 1, False),
    (["document", "--hasLicense", "license-cc-by-4.0", "--count"], 14, 14, False),
    
    # Stakeholders
    (["stakeholder", "--count"], 14, 14, False),
    (["stakeholder", "--isDefinedByTaxonomy", "csiro-responsible-ai-patterns", "--count"], 14, 14, False),
    (["stakeholder", "csiro-stakeholder-ai-technology-producers"], 1, 1, False),
    (["stakeholder", "--isPartOf", "csiro-stakeholder-group-organization-level", "--count"], 2, 2, False),
    
    # Organizations
    (["organization", "--count"], 4, 4, False),
    (["organization", "--grants_license", "license-cc-by-4.0", "--count"], 0, 0, False),
]


@pytest.mark.parametrize("cmd_args,min_count,max_count,byod_required", CLI_TEST_CASES)
def test_cli_api_mode(api_server, cli_command, cmd_args, min_count, max_count, byod_required):
    """Test CLI commands in API mode against expected counts from README."""
    if byod_required:
        pytest.skip("Skipping BYOD test in standard test suite")
    
    # Execute command in API mode
    stdout, stderr, returncode = cli_command(*cmd_args, mode="api", timeout=20)
    
    # Check command succeeded
    assert returncode == 0, f"Command failed with stderr: {stderr}"
    
    # Parse output
    output = stdout.strip()
    
    # If --count flag is in args, output should be a number
    if "--count" in cmd_args:
        try:
            actual_count = int(output)
        except ValueError:
            pytest.fail(f"Expected numeric count, got: {output}")
        
        # Validate count is within expected range
        assert actual_count >= min_count, f"Count {actual_count} less than expected minimum {min_count}"
        if max_count is not None:
            assert actual_count <= max_count, f"Count {actual_count} greater than expected maximum {max_count}"
    else:
        # Command returns full JSON output, should be valid JSON
        import json
        try:
            result = json.loads(output)
            # For single item commands, verify we got a result
            assert result is not None
        except json.JSONDecodeError:
            pytest.fail(f"Expected valid JSON output, got: {output[:200]}")


@pytest.mark.parametrize("cmd_args,min_count,max_count,byod_required", CLI_TEST_CASES)
def test_cli_local_mode(cli_command, cmd_args, min_count, max_count, byod_required):
    """Test CLI commands in local mode against expected counts from README."""
    if byod_required:
        pytest.skip("Skipping BYOD test in standard test suite")
    
    # Execute command in local mode
    stdout, stderr, returncode = cli_command(*cmd_args, mode="local", timeout=30)
    
    # Check command succeeded
    assert returncode == 0, f"Command failed with stderr: {stderr}"
    
    # Parse output
    output = stdout.strip()
    
    # If --count flag is in args, output should be a number
    if "--count" in cmd_args:
        try:
            actual_count = int(output)
        except ValueError:
            pytest.fail(f"Expected numeric count, got: {output}")
        
        # Validate count is within expected range
        assert actual_count >= min_count, f"Count {actual_count} less than expected minimum {min_count}"
        if max_count is not None:
            assert actual_count <= max_count, f"Count {actual_count} greater than expected maximum {max_count}"
    else:
        # Command returns full JSON output, should be valid JSON
        import json
        try:
            result = json.loads(output)
            # For single item commands, verify we got a result
            assert result is not None
        except json.JSONDecodeError:
            pytest.fail(f"Expected valid JSON output, got: {output[:200]}")


@pytest.mark.slow
def test_cli_help(cli_command):
    """Test that CLI help command works."""
    stdout, stderr, returncode = cli_command("--help")
    
    assert returncode == 0
    assert "AI-LinkMO CLI Demo" in stdout
    assert "scope" in stdout


@pytest.mark.slow
def test_cli_invalid_scope(cli_command):
    """Test that CLI rejects invalid scopes."""
    stdout, stderr, returncode = cli_command("invalid_scope_name", "--count")
    
    assert returncode != 0
    assert "invalid choice" in stderr.lower() or "error" in stderr.lower()


@pytest.mark.slow
def test_cli_count_consistency(api_server, cli_command):
    """Test that count results are consistent across multiple calls."""
    # Run same command twice
    stdout1, _, returncode1 = cli_command("risk", "--count", mode="api")
    stdout2, _, returncode2 = cli_command("risk", "--count", mode="api")
    
    assert returncode1 == 0 and returncode2 == 0
    assert stdout1 == stdout2, "Count results should be deterministic"


@pytest.mark.slow 
def test_cli_mode_consistency(api_server, cli_command):
    """Test that API and local modes return same counts."""
    # Test a simple command in both modes
    stdout_api, _, returncode_api = cli_command("principle", "--count", mode="api")
    stdout_local, _, returncode_local = cli_command("principle", "--count", mode="local", timeout=30)
    
    assert returncode_api == 0 and returncode_local == 0
    assert stdout_api.strip() == stdout_local.strip(), "API and local modes should return same counts"
