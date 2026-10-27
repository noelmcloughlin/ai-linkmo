"""Import the gen-pydantic datamodel and find its models by class name."""

from __future__ import annotations

import importlib
import inspect
from enum import Enum
from functools import lru_cache
from types import ModuleType

from linkml_runtime.utils.formatutils import camelcase
from pydantic import BaseModel

from . import settings
from .schema import schema_view


@lru_cache(maxsize=1)
def datamodel() -> ModuleType:
    settings.add_module_paths()
    module = importlib.import_module(settings.DATAMODEL_MODULE)
    _accept_strings_for_valueless_enums(module)
    return module


def model(class_name: str) -> type[BaseModel]:
    """The pydantic model gen-pydantic wrote for a class."""
    module = datamodel()
    for name in (class_name, camelcase(class_name)):
        candidate = getattr(module, name, None)
        if inspect.isclass(candidate) and issubclass(candidate, BaseModel):
            return candidate
    raise LookupError(f"{settings.DATAMODEL_MODULE} has no model for the class {class_name}")


def _string_schema(cls, source, handler):
    from pydantic_core import core_schema

    return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())


def _accept_strings_for_valueless_enums(module: ModuleType) -> None:
    """Let a model take a plain string where the schema has an enum without values.

    gen-pydantic writes such an enum as a bare ``str`` subclass. Pydantic then accepts only
    instances of that subclass, so every value read from a file fails, and FastAPI cannot
    describe the field in its contract. Giving the subclass a string schema and rebuilding
    the models fixes both. This can be removed once pydanticgen writes these enums as plain
    strings (linkml/linkml#4100).
    """
    patched = False
    for name, enum in schema_view().all_enums().items():
        if enum.permissible_values:
            continue
        cls = getattr(module, camelcase(name), None) or getattr(module, name, None)
        if not inspect.isclass(cls) or not issubclass(cls, str) or issubclass(cls, Enum):
            continue
        if "__get_pydantic_core_schema__" not in vars(cls):
            cls.__get_pydantic_core_schema__ = classmethod(_string_schema)
            patched = True
    if not patched:
        return
    models = [
        obj
        for obj in vars(module).values()
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__module__ == module.__name__
    ]
    # A model rebuilt before a model it nests keeps the old nested schema, so twice.
    for _ in range(2):
        for cls in models:
            cls.model_rebuild(force=True)
