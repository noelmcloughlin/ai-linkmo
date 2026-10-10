"""Write the entity list the Svelte UI is built from.

The web UI needs the same list of classes the API exposes, under the same keys, so that a
left-aside entry and an API route never drift apart. The list used to be typed by hand in
``lib/frontend/src/lib/constants.ts``. This script derives it from ``lib/api/api.yaml``
through ``lib.api.exposure.load_exposure()``, the same reader the CLI and the API kernels
use, and writes it as ``lib/frontend/src/lib/entities.json``. ``constants.ts`` imports that
file and merges a small hand-written overlay over it for what the schema cannot know, such as
the accordion groups and the filters a maintainer wants shown.

Each endpoint carries a derived default filter list and prominent field list. The UI only
uses them where its overlay says nothing, so they are a fallback for a newly exposed class,
not a judgement about the best filters for an old one.

Run it through ``just gen-ui-config``. ``lib/test/test_ui_config.py`` fails when the
committed file is behind the exposure file or the schema.
"""

from __future__ import annotations

import json
import re
import sys
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

# The justfile runs this script by path, which puts scripts/ rather than the project root on
# sys.path, so the root is added here. The project import itself stays inside build_config so
# that the test can import this module without loading the schema.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if TYPE_CHECKING:
    from lib.api.exposure import ExposedClass, Exposure

# Slots every entity has that say nothing a reader would filter on. The mappings slots
# are mapping lists to other vocabularies and belong in the record body, not in a filter.
HOUSEKEEPING_SLOTS = frozenset(
    {
        "id",
        "name",
        "description",
        "url",
        "dateCreated",
        "dateModified",
        "notes",
        "exact_mappings",
        "close_mappings",
        "related_mappings",
        "narrow_mappings",
        "broad_mappings",
    }
)

# A filter row costs vertical space in the right aside, so the default list stops here.
MAX_DEFAULT_FILTERS = 8
# Prominent fields come first on a card: the three identity fields, then the first
# references the record makes.
MAX_PROMINENT_REFERENCES = 3
IDENTITY_FIELDS = ("id", "name", "description")

# Where a derived label reads worse than a plain word, say so here rather than in the UI.
# The UI overlay can still replace any label; this table only improves the default.
LABELS = {
    "Documentation": "Documents",
}


def words(class_name: str) -> list[str]:
    """Split a class name into words, keeping an acronym such as LLM together."""
    return re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", class_name)


def plural(word: str) -> str:
    if word.endswith("y") and not word.endswith(("ay", "ey", "oy", "uy")):
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    return word + "s"


def label_for(class_name: str) -> str:
    """A readable plural: ``RiskTaxonomy`` gives ``Risk Taxonomies``."""
    if class_name in LABELS:
        return LABELS[class_name]
    parts = words(class_name)
    parts[-1] = plural(parts[-1])
    return " ".join(parts)


def reference_slots(exposure: Exposure, exposed: ExposedClass) -> list[str]:
    """The class's slots that point at another class or an enum, in schema order.

    ``Any`` is the range LinkML gives a slot with no fixed target, so it is not treated as a
    reference. A slot of a primitive type, such as ``risk_type``, is left to the overlay.
    """
    view = exposure.schema_view
    classes = view.all_classes()
    enums = view.all_enums()
    names = []
    for slot in view.class_induced_slots(exposed.name):
        if slot.name in HOUSEKEEPING_SLOTS:
            continue
        if slot.range in enums or (slot.range in classes and slot.range != "Any"):
            names.append(slot.name)
    return names


def byo_section(exposure: Exposure, exposed: ExposedClass) -> str:
    """The top-level key a bring-your-own-data file keeps this class under.

    Those files are ``Container`` instances, so the key is a ``Container`` slot. The
    library's collection name is that slot when one exists (``groups``, ``adapters``);
    otherwise the slot of the nearest ancestor is the one the loader reads, which puts a
    ``Risk`` under ``entries`` and a ``Requirement`` under ``rules``.
    """
    view = exposure.schema_view
    by_range = {}
    by_name = {}
    for slot in view.class_induced_slots("Container"):
        by_range.setdefault(slot.range, slot.name)
        by_name[slot.name] = slot.range
    if exposed.collection in by_name:
        return exposed.collection
    for ancestor in view.class_ancestors(exposed.name):
        if ancestor in by_range:
            return by_range[ancestor]
    raise ValueError(f"no Container slot holds {exposed.name}")


def endpoint_entry(exposure: Exposure, exposed: ExposedClass) -> dict:
    references = reference_slots(exposure, exposed)
    return {
        "key": exposed.scope,
        "path": exposed.path,
        "label": label_for(exposed.name),
        "type": exposed.name,
        "byo": byo_section(exposure, exposed),
        "description": exposed.description,
        "filters": references[:MAX_DEFAULT_FILTERS],
        "prominent": [*IDENTITY_FIELDS, *references[:MAX_PROMINENT_REFERENCES]],
    }


def build_config(exposure: Exposure | None = None) -> dict:
    from lib.api.exposure import load_exposure

    exposure = exposure or load_exposure()
    return {
        "generated_by": "just gen-ui-config",
        "source": "lib/api/api.yaml",
        "ai_atlas_nexus": version("ai-atlas-nexus"),
        "endpoints": [endpoint_entry(exposure, c) for c in exposure.classes.values()],
    }


def render(config: dict) -> str:
    return json.dumps(config, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: gen_ui_config.py <output path>", file=sys.stderr)
        return 2
    output = Path(args[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(build_config()), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
