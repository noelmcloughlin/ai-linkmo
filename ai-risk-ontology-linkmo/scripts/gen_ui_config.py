"""Write the entity list a web UI is built from.

A web UI needs the classes the API exposes, under the same keys, so that a menu entry and
an API route always agree. This script derives the list from the exposure file and
the schema, through the same reader the two kernels use, and writes it as JSON. A UI can
merge its own overlay over it for what the schema cannot know, such as menu groups.

Each entry carries a default filter list and a prominent field list, derived from the
class's slots that point at another class or an enum. They are a fallback for a class
the UI's overlay does not mention, not a judgement about the best filters.

Run it with `just gen-ui-config`, which writes it where the entities_file answer says, or
to the path given. tests/test_published.py fails when the committed file is out of date
with the exposure file or the schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Slots that say nothing a reader filters on: names, free text and mapping lists.
HOUSEKEEPING_SLOTS = frozenset(
    {
        "name",
        "description",
        "title",
        "label",
        "url",
        "notes",
        "exact_mappings",
        "close_mappings",
        "related_mappings",
        "narrow_mappings",
        "broad_mappings",
    }
)
MAX_DEFAULT_FILTERS = 8
MAX_PROMINENT_REFERENCES = 3


def reference_slots(exposure, exposed) -> list[str]:
    """The class's slots that point at another class or an enum, in schema order. ``Any``
    is the range LinkML gives a slot with no fixed target, so it is not a reference."""
    view = exposure.schema_view
    classes, enums = view.all_classes(), view.all_enums()
    names = []
    for slot in view.class_induced_slots(exposed.name):
        if slot.name in HOUSEKEEPING_SLOTS or slot.name == exposed.identifier:
            continue
        if slot.range in enums or (slot.range in classes and slot.range != "Any"):
            names.append(slot.name)
    return names


def collection_for(exposure, exposed) -> str | None:
    """The root class's slot that holds this class in a data file, if there is one."""
    from ai_linkmo.schema import collection_slots

    if exposure.root_class is None:
        return None
    view = exposure.schema_view
    by_range: dict[str, str] = {}
    for slot in collection_slots(view, exposure.root_class):
        by_range.setdefault(slot.range, slot.name)
    for ancestor in view.class_ancestors(exposed.name):
        if ancestor in by_range:
            return by_range[ancestor]
    return None


def endpoint_entry(exposure, exposed) -> dict:
    references = reference_slots(exposure, exposed)
    identity = [n for n in (exposed.identifier, "name", "description") if n and exposed.parameter(n)]
    return {
        "key": exposed.scope,
        "path": exposed.path,
        "label": exposed.label,
        "type": exposed.name,
        "collection": collection_for(exposure, exposed),
        "description": exposed.description,
        "filters": references[:MAX_DEFAULT_FILTERS],
        "prominent": [*identity, *references[:MAX_PROMINENT_REFERENCES]],
    }


def build_config(exposure=None) -> dict:
    from ai_linkmo.exposure import load_exposure

    exposure = exposure or load_exposure()
    return {
        "generated_by": "just gen-ui-config",
        "schema": exposure.schema_view.schema.name,
        "schema_version": exposure.schema_view.schema.version,
        "endpoints": [endpoint_entry(exposure, c) for c in exposure.classes.values()],
    }


def render(config: dict) -> str:
    return json.dumps(config, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        output = Path(args[0])
    else:
        from ai_linkmo.settings import entities_path

        output = entities_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(build_config()), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
