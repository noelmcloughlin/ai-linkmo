"""One SchemaView over the project's schema, and the few questions asked of it.

Everything the kernels know about a class, its slots, its identifier and its subclasses,
comes from here, so a slot added to the schema becomes a filter without a code change.
"""

from __future__ import annotations

from functools import lru_cache

from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from . import settings


@lru_cache(maxsize=1)
def schema_view() -> SchemaView:
    """The schema with its imports, built once per process."""
    path = settings.schema_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"The schema {path} does not exist; set {settings.ENV_PREFIX}_SCHEMA "
            "or answer schema_path again with copier update"
        )
    # Modules beside the schema are mapped by name, so that an import written as a bare
    # module name resolves wherever the process starts. LinkML adds .yaml itself.
    importmap = {p.stem: str(p.with_suffix("")) for p in path.parent.glob("*.yaml")}
    return SchemaView(str(path), importmap=importmap, merge_imports=True)


def root_class(view: SchemaView | None = None) -> str | None:
    """The class a data file holds: the answered root class, else the tree_root class."""
    view = view or schema_view()
    if settings.ROOT_CLASS:
        if view.get_class(settings.ROOT_CLASS) is None:
            raise ValueError(f"The root class {settings.ROOT_CLASS} is not in the schema")
        return settings.ROOT_CLASS
    roots = [c.name for c in view.all_classes().values() if c.tree_root]
    return roots[0] if roots else None


def collection_slots(view: SchemaView, class_name: str) -> list[SlotDefinition]:
    """The slots of a class that hold records: multivalued, with a class as range."""
    classes = view.all_classes()
    return [s for s in view.class_induced_slots(class_name) if s.multivalued and s.range in classes]


def identifier_slot(view: SchemaView, class_name: str) -> str | None:
    slot = view.get_identifier_slot(class_name)
    return slot.name if slot is not None else None


def designator_slot(view: SchemaView, class_name: str) -> str | None:
    """The slot whose value names a record's class, such as ``type``, if the class has one."""
    return next((s.name for s in view.class_induced_slots(class_name) if s.designates_type), None)


def subclasses(view: SchemaView, class_name: str) -> list[str]:
    """The class and every class below it, in schema order."""
    below = set(view.class_descendants(class_name))
    return [name for name in view.all_classes() if name in below]
