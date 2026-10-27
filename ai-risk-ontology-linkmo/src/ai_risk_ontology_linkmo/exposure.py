"""Join the exposure file and the schema into one view for the two kernels.

The command-line kernel (``cli.py``) and the API kernel (``api_kernel.py``) ask the same
questions: which classes are exposed, under which path, and which parameters each takes.
The exposure file names the classes, their paths and the operations written by hand. The
LinkML schema gives each class its slots, and each slot becomes one parameter. This module
joins the two, so that neither kernel reads YAML or SchemaView itself.

When the exposure file names no classes, they are derived from the schema: every class a
collection slot of the root class holds, or every concrete class when there is no root,
less the classes the file excludes. ``python -m <package>.exposure`` prints that list in
the file's own format, ready to copy into the file and edit.
"""

from __future__ import annotations

import keyword
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.utils.schemaview import SchemaView

from . import settings
from .schema import collection_slots, identifier_slot, root_class, schema_view

# LinkML types that are not strings, by the root of their typeof chain. Everything else,
# including references to other classes, enums and dates, is passed as a string.
_KIND_BY_TYPE = {
    "integer": "integer",
    "float": "number",
    "double": "number",
    "decimal": "number",
    "boolean": "boolean",
}


@dataclass(frozen=True)
class Parameter:
    """One query parameter of a class listing, which is also one command-line option."""

    name: str
    kind: str = "string"  # "string", "boolean", "integer", "number", "array" or "object"
    description: str = ""
    # The permissible values when the slot's range is an enum with values. An enum
    # without values is a free string.
    choices: tuple[str, ...] = ()
    # A multivalued slot still takes one value: a record matches when its list holds it.
    multivalued: bool = False
    # True for a slot of the class, False for a parameter the exposure file adds.
    slot: bool = True

    @property
    def python_name(self) -> str:
        """The name as a Python identifier; a slot named ``from`` becomes ``from_``."""
        name = re.sub(r"\W", "_", self.name)
        if not name or name[0].isdigit():
            name = f"_{name}"
        return f"{name}_" if keyword.iskeyword(name) else name


@dataclass(frozen=True)
class ExposedClass:
    """A class the API lists and the command line offers as a command."""

    name: str
    path: str
    operation_id: str
    label: str
    description: str
    # The slot that names one record, if the class has one; giving it fetches that record.
    identifier: str | None
    parameters: tuple[Parameter, ...]

    @property
    def scope(self) -> str:
        """The command's name, which is the path without its slash: ``/dog`` is ``dog``."""
        return self.path.strip("/")

    @property
    def slot_names(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.parameters if p.slot)

    def parameter(self, name: str) -> Parameter | None:
        return next((p for p in self.parameters if p.name == name), None)


@dataclass(frozen=True)
class Exposure:
    classes: dict[str, ExposedClass]
    overlay: dict[str, Any]
    root_class: str | None
    derived: bool
    schema_view: SchemaView = field(repr=False, compare=False)

    @property
    def by_scope(self) -> dict[str, ExposedClass]:
        return {c.scope: c for c in self.classes.values()}

    @property
    def by_path(self) -> dict[str, ExposedClass]:
        return {c.path: c for c in self.classes.values()}

    @property
    def hand_paths(self) -> dict[str, Any]:
        """The operations written by hand, as OpenAPI path items keyed by path."""
        return self.overlay.get("paths") or {}


def words(class_name: str) -> list[str]:
    """Split a class name into words, keeping an acronym such as LLM together."""
    return re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", class_name) or [class_name]


def plural(word: str) -> str:
    if word.endswith("y") and not word.endswith(("ay", "ey", "oy", "uy")):
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    return word + "s"


def default_path(class_name: str) -> str:
    """``PetOwner`` is served at ``/pet-owner``."""
    return "/" + "-".join(w.lower() for w in words(class_name))


def default_operation_id(class_name: str) -> str:
    return "list_" + "_".join(w.lower() for w in words(class_name))


def default_label(class_name: str) -> str:
    """A readable plural for a menu: ``RiskTaxonomy`` is ``Risk Taxonomies``."""
    parts = words(class_name)
    parts[-1] = plural(parts[-1])
    return " ".join(parts)


def derived_classes(view: SchemaView, root: str | None, excluded: set[str]) -> list[str]:
    """The classes exposed when the exposure file names none."""
    if root is not None:
        names = [slot.range for slot in collection_slots(view, root)]
    else:
        names = [c.name for c in view.all_classes().values() if not c.abstract and not c.mixin]
    return [name for name in dict.fromkeys(names) if name not in excluded]


def _parameter_from_slot(view: SchemaView, slot) -> Parameter:
    choices: tuple[str, ...] = ()
    kind = "string"
    enums = view.all_enums()
    if slot.range in enums:
        choices = tuple(enums[slot.range].permissible_values.keys())
    elif slot.range in view.all_types():
        kind = _KIND_BY_TYPE.get(view.type_ancestors(slot.range)[-1], "string")
    return Parameter(
        name=slot.name,
        kind=kind,
        description=" ".join((slot.description or "").split()),
        choices=choices,
        multivalued=bool(slot.multivalued),
    )


def _extra_parameter(overlay: dict[str, Any], name: str) -> Parameter:
    """A parameter the exposure file adds beside the slots, from the overlay's components."""
    definitions = (overlay.get("components") or {}).get("parameters") or {}
    if name not in definitions:
        raise ValueError(f"The exposure file adds the parameter {name} but does not define it")
    definition = definitions[name]
    return Parameter(
        name=definition.get("name", name),
        kind=(definition.get("schema") or {}).get("type", "string"),
        description=" ".join((definition.get("description") or "").split()),
        choices=tuple((definition.get("schema") or {}).get("enum") or ()),
        slot=False,
    )


def read_exposure_file(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        document = yaml.safe_load(handle) or {}
    return (document.get("generator_args") or {}).get("openapi") or {}


@lru_cache(maxsize=None)
def load_exposure(path: Path | None = None) -> Exposure:
    """Read the exposure file once and resolve every exposed class against the schema."""
    path = path or settings.exposure_path()
    config = read_exposure_file(path)
    expose = config.get("expose") or {}
    overlay = config.get("overlay") or {}
    excluded = set((config.get("exclude") or {}).get("classes") or ())
    view = schema_view()
    root = root_class(view)
    entries = expose.get("classes")
    derived = entries is None
    if derived:
        entries = {name: {} for name in derived_classes(view, root, excluded)}
    elif isinstance(entries, list):
        entries = {name: {} for name in entries}
    common = list(expose.get("parameters") or ())
    classes: dict[str, ExposedClass] = {}
    for name, entry in entries.items():
        if name in excluded:
            continue
        entry = entry or {}
        definition = view.get_class(name)
        if definition is None:
            raise ValueError(f"{path.name} exposes {name}, which the schema does not define")
        parameters = [_parameter_from_slot(view, s) for s in view.class_induced_slots(name)]
        slot_names = {p.name for p in parameters}
        for extra in dict.fromkeys(common + list(entry.get("parameters") or ())):
            if extra not in slot_names:
                parameters.append(_extra_parameter(overlay, extra))
        classes[name] = ExposedClass(
            name=name,
            path=entry.get("path", default_path(name)),
            operation_id=entry.get("operation_id", default_operation_id(name)),
            label=entry.get("label", default_label(name)),
            description=" ".join((definition.description or "").split()),
            identifier=identifier_slot(view, name),
            parameters=tuple(parameters),
        )
    return Exposure(classes=classes, overlay=overlay, root_class=root, derived=derived, schema_view=view)


def render_entries(exposure: Exposure) -> str:
    """The exposed classes in the exposure file's format, to copy into it and edit."""
    entries = {
        c.name: {"path": c.path, "operation_id": c.operation_id, "label": c.label}
        for c in exposure.classes.values()
    }
    return yaml.safe_dump({"classes": entries}, sort_keys=False)


def main() -> int:
    exposure = load_exposure()
    source = "derived from the root class" if exposure.derived else "named in the exposure file"
    print(f"# {len(exposure.classes)} classes, {source}; root class: {exposure.root_class}")
    for exposed in exposure.classes.values():
        print(f"# {exposed.path}: {len(exposed.parameters)} parameters")
    print(render_entries(exposure), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
