"""The exposure file, the schema and the datamodel agree with each other.

These are the invariants both kernels rely on: every exposed class is a schema class with
a model, every slot of the class is a parameter, and enum slots offer their values.
"""

from __future__ import annotations

from ai_linkmo.datamodel import model


def test_every_exposed_class_is_in_the_schema_and_has_a_model(exposure):
    for exposed in exposure.classes.values():
        assert exposure.schema_view.get_class(exposed.name) is not None, exposed.name
        assert model(exposed.name).__name__, exposed.name


def test_paths_and_operation_ids_are_unique(exposure):
    paths = [c.path for c in exposure.classes.values()]
    operation_ids = [c.operation_id for c in exposure.classes.values()]
    assert len(set(paths)) == len(paths)
    assert len(set(operation_ids)) == len(operation_ids)
    assert not set(paths) & set(exposure.hand_paths)


def test_the_parameters_are_the_slots_of_their_class(exposure):
    view = exposure.schema_view
    for exposed in exposure.classes.values():
        slots = [s.name for s in view.class_induced_slots(exposed.name)]
        assert list(exposed.slot_names) == slots, exposed.name


def test_enum_slots_offer_their_values(exposure):
    view = exposure.schema_view
    enums = view.all_enums()
    for exposed in exposure.classes.values():
        for slot in view.class_induced_slots(exposed.name):
            parameter = exposed.parameter(slot.name)
            if slot.range in enums:
                # An enum without values is a free string.
                assert parameter.choices == tuple(enums[slot.range].permissible_values), slot.name
            else:
                assert parameter.choices == (), slot.name
