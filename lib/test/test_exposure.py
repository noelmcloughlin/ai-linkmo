"""The exposure file, the schema and the library agree with each other.

These are the invariants the kernels rely on: every exposed class is a schema class,
every filter is a slot of its class, and the generic
``query_class`` answers the way the old per-class handlers did.
"""

from __future__ import annotations

import pytest

from lib.api.exposure import Parameter, load_exposure


@pytest.fixture(scope="module")
def exposure():
    return load_exposure()


def test_every_exposed_class_is_in_the_schema(exposure):
    for exposed in exposure.classes.values():
        assert exposure.schema_view.get_class(exposed.name) is not None


def test_paths_and_operation_ids_are_unique(exposure):
    paths = [c.path for c in exposure.classes.values()]
    operation_ids = [c.operation_id for c in exposure.classes.values()]
    assert len(set(paths)) == len(paths)
    assert len(set(operation_ids)) == len(operation_ids)
    assert not set(paths) & set(exposure.hand_paths)


def test_filters_are_slots_of_their_class(exposure):
    view = exposure.schema_view
    for exposed in exposure.classes.values():
        slots = {s.name for s in view.class_induced_slots(exposed.name)}
        assert set(exposed.slot_names) == slots, exposed.name
        extras = {p.name for p in exposed.parameters if not p.slot}
        expected = {"byod"}
        if exposed.related:
            expected |= {"related", "related_ids", "hasRelatedRisk"} - slots
        assert extras == expected, exposed.name


def test_enum_slots_offer_their_values(exposure):
    adapter_type = exposure.classes["Adapter"].parameter("hasAdapterType")
    assert adapter_type is not None and "LORA" in adapter_type.choices
    assert adapter_type.multivalued
    # An enum without permissible values is a free string.
    jurisdiction = exposure.classes["Risk"].parameter("hasJurisdiction")
    assert jurisdiction is not None and jurisdiction.choices == ()


def test_numeric_slots_have_a_numeric_kind(exposure):
    model = exposure.classes["LargeLanguageModel"]
    assert model.parameter("numParameters") == Parameter(
        name="numParameters",
        kind="integer",
        description=model.parameter("numParameters").description,
    )


def test_related_classes_have_a_lookup(exposure):
    from lib.api.handlers import RELATED_LOOKUPS

    related = {c.name for c in exposure.classes.values() if c.related}
    assert related - {"Risk"} == set(RELATED_LOOKUPS)


@pytest.mark.slow
@pytest.mark.parametrize(
    "class_name,kwargs,count",
    [
        ("Risk", {"isDefinedByTaxonomy": "nist-ai-rmf"}, 12),
        ("Risk", {"isPartOf": "granite-guardian-harm-group"}, 7),
        ("Risk", {"id": "atlas-toxic-output", "related_ids": True}, 14),
        ("Group", {"type": "CapabilityGroup"}, 8),
        ("ControlActivityObligation", {"hasEvidenceCategory": "TECHNICAL_IMPLEMENTATION"}, 48),
        ("ControlActivityObligation", {"hasTypicalLocation": "Engineering Practice"}, 6),
        ("Adapter", {"hasAdapterType": "LORA"}, 19),
        ("Adapter", {"hasRelatedRisk": "granite-relevance"}, 1),
        ("Action", {"hasRelatedRisk": "nist-human-ai-configuration"}, 53),
        ("Action", {"hasRelatedRisk": "atlas-toxic-output", "related_ids": True}, 47),
        ("RiskControl", {"detectsRiskConcept": "shieldgemma-dangerous-content"}, 1),
        ("RiskControl", {"hasRelatedRisk": "atlas-toxic-output", "related": True}, 4),
        ("RiskIncident", {"hasRelatedRisk": "atlas-dangerous-use"}, 2),
        ("LLMIntrinsic", {"hasRelatedRisk": "granite-answer-relevance", "related": True}, 6),
        ("Stakeholder", {"isPartOf": "csiro-stakeholder-group-organization-level"}, 2),
    ],
)
def test_query_class_counts(class_name, kwargs, count):
    from lib.api.handlers import query_class

    assert query_class(class_name, **kwargs)["count"] == count


@pytest.mark.slow
def test_query_class_single_record_and_unknown_filter():
    from fastapi import HTTPException

    from lib.api.handlers import query_class

    assert query_class("RiskTaxonomy", id="nist-ai-rmf")["item"]["id"] == "nist-ai-rmf"
    assert query_class("RiskTaxonomy", id="no-such-taxonomy")["item"] is None
    with pytest.raises(HTTPException) as caught:
        query_class("Risk", nosuchslot="x")
    assert caught.value.status_code == 422
