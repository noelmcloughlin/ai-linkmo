"""The store and the library answer the plain listings alike.

``AI_LINKMO_DATA_SOURCE`` chooses the source. These tests ask the same questions of both and
compare the answers, so a difference between linkml-store's filters and the library's shows
up here rather than in a user's terminal.
"""

from __future__ import annotations

import pytest

from lib.store.loader import database_path

pytestmark = pytest.mark.skipif(
    not database_path(False).exists(), reason="run `just load-store` to build the store"
)

CASES = [
    ("RiskTaxonomy", {}),
    ("Risk", {"isDefinedByTaxonomy": "nist-ai-rmf"}),
    ("Risk", {"isPartOf": "granite-guardian-harm-group"}),
    ("Risk", {"descriptor": "specific to generative AI"}),
    ("Group", {"type": "CapabilityGroup"}),
    ("ControlActivityObligation", {"hasEvidenceCategory": "TECHNICAL_IMPLEMENTATION"}),
    ("ControlActivityObligation", {"hasTypicalLocation": "Engineering Practice"}),
    ("Adapter", {"hasAdapterType": "LORA"}),
    ("LargeLanguageModel", {"performsTask": "code-generation"}),
    ("LargeLanguageModel", {"isProvidedBy": "google"}),
    ("Stakeholder", {"isPartOf": "csiro-stakeholder-group-organization-level"}),
    ("Action", {"hasAiActorTask": "Human Factors"}),
    ("RiskControl", {}),
    ("Requirement", {}),
]


def _answer(monkeypatch, source: str, class_name: str, **kwargs):
    from lib.api.handlers import query_class

    monkeypatch.setenv("AI_LINKMO_DATA_SOURCE", source)
    return query_class(class_name, **kwargs)


@pytest.mark.parametrize("class_name,filters", CASES)
def test_both_sources_return_the_same_records(monkeypatch, class_name, filters):
    from_store = _answer(monkeypatch, "store", class_name, **filters)
    from_library = _answer(monkeypatch, "library", class_name, **filters)
    assert from_store["count"] == from_library["count"]
    assert {r["id"] for r in from_store["items"]} == {r["id"] for r in from_library["items"]}
    assert from_store["validation_errors"] == from_library["validation_errors"] == []


def test_a_record_reads_the_same_from_both_sources(monkeypatch):
    from_store = _answer(monkeypatch, "store", "Risk", id="atlas-toxic-output")["item"]
    from_library = _answer(monkeypatch, "library", "Risk", id="atlas-toxic-output")["item"]
    assert from_store == from_library


def test_the_store_rejects_an_unknown_taxonomy_like_the_library(monkeypatch):
    from fastapi import HTTPException

    for source in ("store", "library"):
        with pytest.raises(HTTPException) as caught:
            _answer(monkeypatch, source, "Risk", isDefinedByTaxonomy="no-such-taxonomy")
        assert caught.value.status_code == 400


def test_the_store_does_not_load_the_library(monkeypatch):
    import sys

    monkeypatch.setenv("AI_LINKMO_DATA_SOURCE", "store")
    loaded_before = "ai_atlas_nexus.library" in sys.modules
    from lib.api.handlers import query_class

    assert query_class("RiskTaxonomy", id="nist-ai-rmf")["item"]["id"] == "nist-ai-rmf"
    assert loaded_before or "ai_atlas_nexus.library" not in sys.modules
