"""One example record per class, taken from the data, for gen-doc's ``--example-directory``.

gen-doc adds an "Examples" section to a class page when the directory given by
``--example-directory`` holds files named ``<Class>-<name>.yaml``. It matches a file to a
class by that name prefix and shows the file as it is. linkml-project-copier leaves the
option off, so the schema's pages carry no instance data. This module fills the directory
from the project's data source: for each concrete class with records, the record whose
identifier sorts first, written as YAML on its own. An abstract class gets no example even
when the data has records of it, since the schema says nothing is an instance of it. It is
generalised from ai-linkmo's scripts/gen_examples.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.utils.schemaview import SchemaView


def example_file(class_name: str, identifier: str) -> str:
    """The file name gen-doc looks for: the class, a hyphen, then the identifier made safe.

    Characters other than letters, digits, dots, hyphens and underscores, such as the colon
    of a CURIE or a slash, become underscores so that the identifier is a valid file name.
    """
    return f"{class_name}-{re.sub(r'[^A-Za-z0-9._-]+', '_', identifier)}.yaml"


def choose_examples(view: SchemaView, rows: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """The example record of each concrete class with records, keyed by class. It is the
    record whose identifier sorts first, so it changes only when the data does."""
    examples = {}
    for class_name in sorted(rows):
        definition = view.get_class(class_name)
        if definition is None or definition.abstract or not rows[class_name]:
            continue
        key = view.get_identifier_slot(class_name)
        records = rows[class_name]
        if key is not None:
            records = sorted(records, key=lambda record: str(record.get(key.name, "")))
        examples[class_name] = records[0]
    return examples


def identifier_of(view: SchemaView, class_name: str, record: dict[str, Any]) -> str:
    key = view.get_identifier_slot(class_name)
    return str(record.get(key.name)) if key is not None and key.name in record else "001"


def write_examples(view: SchemaView, examples: dict[str, dict[str, Any]], directory: Path) -> list[Path]:
    """Write each example to ``directory``, after removing the examples a previous run left.
    Only files named after a class of the schema and a hyphen are removed."""
    directory.mkdir(parents=True, exist_ok=True)
    classes = view.all_classes()
    for stale in directory.glob("*-*.yaml"):
        if stale.name.split("-", 1)[0] in classes:
            stale.unlink()
    paths = []
    for class_name, record in examples.items():
        path = directory / example_file(class_name, identifier_of(view, class_name, record))
        path.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
        paths.append(path)
    return paths


def validate_examples(view: SchemaView, examples: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Validate each example against its class with linkml's validator, closed, so that a
    key the class does not have is an error too. Needs the linkml package."""
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin

    validator = Validator(view.schema, validation_plugins=[JsonschemaValidationPlugin(closed=True)])
    failures = {}
    for class_name, record in examples.items():
        report = validator.validate(record, class_name)
        if report.results:
            failures[class_name] = [result.message for result in report.results]
    return failures
