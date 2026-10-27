"""Where the records come from: a directory of YAML instance files, or a Python object.

A source answers one question, ``query(class_name, **filters)``: the records of a class
and of its subclasses whose slots hold the given values. A record matches a filter when
the slot equals the value or, for a multivalued slot, when its list holds the value.

``YamlDirectory`` reads every ``.yaml``, ``.yml`` and ``.json`` file under a directory once.
A file whose name starts with a class name and a dash, as in ``Person-001.yaml``, holds
records of that class. Any other file holds an instance of the root class, or a list of
them, whose collection slots hold the records.

Two records that share an identifier are one record when one's class is the other's or an
ancestor of it, such as a record and the mapping rows another file adds to it. They are
merged before they are validated: a list gains the values it lacks, and any other value is
replaced. Records of unrelated classes that happen to share a value are both kept.

Each record is then built with the model of its own class. The record's designator slot
names that class when it has one. Otherwise the model is the first of the slot's range and
its subclasses that accepts the record, which is the choice pydantic makes for a union of
them. A record no model accepts is left out, and its error is kept for the listing's
``validation_errors``.

``ObjectSource`` wraps any object with a ``query(class_name, **filters)`` method and
passes the question on unchanged, including the parameters the exposure file adds.
"""

from __future__ import annotations

import datetime
import importlib
import inspect
import logging
from collections import defaultdict
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import yaml
from pydantic import BaseModel, ValidationError

from . import settings
from .datamodel import model
from .schema import collection_slots, designator_slot, identifier_slot, root_class, schema_view, subclasses

logger = logging.getLogger(__name__)

_SUFFIXES = (".yaml", ".yml", ".json")


class UnknownFilter(ValueError):
    """A filter that names no slot of the class."""


class Source(Protocol):
    def query(self, class_name: str, **filters: Any) -> list[Any]: ...


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def _same(field: Any, value: Any) -> bool:
    if isinstance(field, BaseModel):
        # An inlined object matches by its identifier, or by its first value.
        dumped = field.model_dump(mode="json", exclude_none=True)
        field = dumped.get("id", next(iter(dumped.values()), None))
    elif isinstance(field, dict):
        field = field.get("id", next(iter(field.values()), None))
    field = _plain(field)
    if field == value:
        return True
    if isinstance(field, bool) or isinstance(value, bool):
        return str(field).lower() == str(value).lower()
    return str(field) == str(value)


def field_value(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    if name in type(record).model_fields:
        return getattr(record, name)
    # A field whose Python name differs from the slot's, such as ``from_``, carries the
    # slot name as its alias.
    for python_name, info in type(record).model_fields.items():
        if info.alias == name:
            return getattr(record, python_name)
    return None


def matches(record: Any, name: str, value: Any) -> bool:
    field = field_value(record, name)
    if field is None:
        return False
    if isinstance(field, (list, tuple, set)):
        return any(_same(item, value) for item in field)
    return _same(field, value)


def check_filters(class_name: str, filters: dict[str, Any]) -> None:
    slots = {s.name for s in schema_view().class_induced_slots(class_name)}
    unknown = sorted(set(filters) - slots)
    if unknown:
        raise UnknownFilter(f"{class_name} has no slot named {', '.join(unknown)}")


def _describe(exc: Exception) -> str:
    """A validation error on one line: each field with what was wrong with it."""
    if isinstance(exc, ValidationError):
        return "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'record'}: {e['msg']} (read {e.get('input')!r})"
            for e in exc.errors()
        )
    return str(exc)


def _merge(into: dict[str, Any], other: dict[str, Any]) -> None:
    for key, value in other.items():
        if isinstance(into.get(key), list) and isinstance(value, list):
            into[key] = into[key] + [item for item in value if item not in into[key]]
        else:
            into[key] = value


class YamlDirectory:
    """Every record in a directory of YAML instance files, read once and kept in memory."""

    def __init__(self, directory: Path):
        if not directory.is_dir():
            raise FileNotFoundError(
                f"The data directory {directory} does not exist; set {settings.ENV_PREFIX}_DATA "
                "or answer data_path again with copier update"
            )
        self.directory = directory
        self.records: list[tuple[str, BaseModel]] = []
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.files = 0
        self._load()

    def _load(self) -> None:
        view = schema_view()
        root = root_class(view)
        classes = view.all_classes()
        # The records with an identifier, keyed by it. One key holds one entry per class
        # lineage, so a Person and a Shelter that share a value stay two records.
        keyed: dict[Any, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        loose: list[tuple[str, dict[str, Any]]] = []

        def add(range_name: str, item: Any) -> None:
            if not isinstance(item, dict):
                self.errors[range_name].append(f"{range_name}: expected a mapping, read {item!r}")
                return
            key_slot = identifier_slot(view, range_name)
            key = item.get(key_slot) if key_slot else None
            if key is None or isinstance(key, (dict, list)):
                loose.append((range_name, dict(item)))
                return
            for index, (other, data) in enumerate(keyed[key]):
                if range_name == other or range_name in view.class_ancestors(other):
                    _merge(data, item)
                    return
                if other in view.class_ancestors(range_name):
                    # The same record, listed under a subclass: the subclass names it.
                    _merge(data, item)
                    keyed[key][index] = (range_name, data)
                    return
            keyed[key].append((range_name, dict(item)))

        for path in sorted(p for p in self.directory.rglob("*") if p.suffix in _SUFFIXES and p.is_file()):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            if document is None:
                continue
            self.files += 1
            prefix = path.name.split("-", 1)[0]
            target = prefix if prefix in classes and prefix != path.name else root
            if target is None:
                self.errors["*"].append(f"{path.name}: no class in the file name and no root class")
                continue
            documents = document if isinstance(document, list) else [document]
            if target == root:
                for instance in documents:
                    if not isinstance(instance, dict):
                        self.errors["*"].append(f"{path.name}: expected a mapping of {root}, read {instance!r}")
                        continue
                    for slot in collection_slots(view, root):
                        value = instance.get(slot.name)
                        if isinstance(value, dict):
                            # A collection inlined as a dictionary is keyed by identifier.
                            key_slot = identifier_slot(view, slot.range) or "id"
                            value = [
                                {key_slot: key, **(item if isinstance(item, dict) else {})}
                                for key, item in value.items()
                            ]
                        for item in value or ():
                            add(slot.range, item)
            else:
                for item in documents:
                    add(target, item)

        for range_name, data in [*(entry for entries in keyed.values() for entry in entries), *loose]:
            self._build(range_name, data)
        logger.info("Read %d records from %d files under %s", len(self.records), self.files, self.directory)

    def _build(self, range_name: str, data: dict[str, Any]) -> None:
        view = schema_view()
        classes = view.all_classes()
        key_slot = identifier_slot(view, range_name)
        key = data.get(key_slot, "?") if key_slot else "?"
        designator = designator_slot(view, range_name)
        named = data.get(designator) if designator else None
        if named:
            # A designator may hold a class name, a CURIE or a URI; the local name decides.
            local = str(named).replace("#", "/").replace(":", "/").rsplit("/", 1)[-1]
            if local not in classes:
                # Keyed by the collection's class, so that its listing reports the record.
                self.errors[range_name].append(
                    f"{range_name} {key}: {designator} names {named!r}, which the schema does not define"
                )
                return
            candidates = [local]
        else:
            candidates = [range_name, *(c for c in subclasses(view, range_name) if c != range_name)]
        first_error: str | None = None
        # The datamodel has a model for every class, abstract and mixin ones included, and
        # real data uses them, so the schema's flags are not a reason to skip a class.
        for name in candidates:
            try:
                self.records.append((name, model(name)(**data)))
                return
            except (ValidationError, TypeError, LookupError) as exc:
                first_error = first_error or f"{name} {key}: {_describe(exc)}"
        self.errors[candidates[0]].append(first_error or f"{range_name} {key}: no concrete class accepts it")

    def query(self, class_name: str, **filters: Any) -> list[BaseModel]:
        check_filters(class_name, filters)
        wanted = set(subclasses(schema_view(), class_name))
        return [
            record
            for name, record in self.records
            if name in wanted and all(matches(record, k, v) for k, v in filters.items())
        ]

    def errors_for(self, class_name: str) -> list[str]:
        return [e for name in subclasses(schema_view(), class_name) for e in self.errors.get(name, ())]


class ObjectSource:
    """A Python object that answers ``query(class_name, **filters)`` itself."""

    def __init__(self, spec: str):
        module_name, _, attribute = spec.partition(":")
        if not module_name or not attribute:
            raise ValueError(f"The data object {spec!r} is not written as module:attribute")
        settings.add_module_paths()
        obj = getattr(importlib.import_module(module_name), attribute)
        if inspect.isclass(obj) or (callable(obj) and not hasattr(obj, "query")):
            obj = obj()
        if not callable(getattr(obj, "query", None)):
            raise TypeError(f"{spec} has no query(class_name, **filters) method")
        self.obj = obj

    def query(self, class_name: str, **filters: Any) -> list[Any]:
        return list(self.obj.query(class_name, **filters) or [])

    def errors_for(self, class_name: str) -> list[str]:
        errors_for = getattr(self.obj, "errors_for", None)
        return list(errors_for(class_name)) if callable(errors_for) else []


@lru_cache(maxsize=1)
def load_source() -> Source:
    """The configured source, built once per process."""
    if settings.DATA_SOURCE == "yaml":
        return YamlDirectory(settings.data_path())
    if settings.DATA_SOURCE == "python":
        return ObjectSource(settings.DATA)
    raise ValueError(
        f"{settings.ENV_PREFIX}_DATA_SOURCE must be yaml or python, not {settings.DATA_SOURCE!r}. If the "
        "host uses that name for a setting of its own, answer env_prefix again with copier update."
    )


def reset_source() -> None:
    """Forget the loaded records, after the data changes."""
    load_source.cache_clear()


def _own_class(view, record: Any, fallback: str) -> str:
    """The class a record belongs to: its model's, else the class its designator names."""
    classes = view.all_classes()
    if isinstance(record, BaseModel) and type(record).__name__ in classes:
        return type(record).__name__
    if isinstance(record, dict):
        designator = designator_slot(view, fallback)
        named = record.get(designator) if designator else None
        local = str(named).replace("#", "/").replace(":", "/").rsplit("/", 1)[-1] if named else None
        if local in classes:
            return local
    return fallback


def _typed(kind: str, value: Any) -> Any:
    """A parameter's value given as text, typed as the kernels type it."""
    if not isinstance(value, str):
        return value
    if kind == "boolean":
        return value.strip().lower() in ("1", "true", "yes", "on")
    if kind == "integer":
        return int(value)
    if kind == "number":
        return float(value)
    return value


def rows_by_class(source: Source | None = None, params: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Every record as a plain dict under its slot names, grouped by its own class.

    The browse build and the class examples read the data this way. A YAML directory gives
    its records as read. Any other source is asked for every exposed class, and a record
    that two listings return, such as a subclass's record in its parent's listing, is kept
    once under its own class. ``params``, such as a parameter the exposure file adds to
    bring in more data, are passed with each question to every class that takes them.
    """
    from .exposure import load_exposure

    source = source or load_source()
    view = schema_view()
    if isinstance(source, YamlDirectory) and not params:
        pairs = list(source.records)
    else:
        pairs = []
        for exposed in load_exposure().classes.values():
            given = {
                name: _typed(parameter.kind, value)
                for name, value in (params or {}).items()
                if (parameter := exposed.parameter(name)) is not None
            }
            pairs += [(_own_class(view, record, exposed.name), record) for record in source.query(exposed.name, **given)]
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for class_name, record in pairs:
        if isinstance(record, BaseModel):
            data = record.model_dump(mode="json", by_alias=True, exclude_none=True)
        elif isinstance(record, dict):
            data = {k: _plain(v) for k, v in record.items() if v is not None}
        else:
            continue
        key_slot = identifier_slot(view, class_name)
        if key_slot and key_slot in data:
            if (class_name, str(data[key_slot])) in seen:
                continue
            seen.add((class_name, str(data[key_slot])))
        rows[class_name].append(data)
    return dict(rows)
