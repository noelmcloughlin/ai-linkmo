"""Write one example per class, taken from the data, for gen-doc's ``--example-directory``.

gen-doc adds an "Examples" section to a class page when the directory given by
``--example-directory`` holds files named ``<Class>-<name>.yaml``. It matches a file to a
class by that name prefix and shows the file as it is. linkml-project-copier leaves the
option off, so the schema's pages carry no instance data. This script fills the directory
from the data: for each concrete class that has records, the record whose identifier sorts
first, written as YAML on its own and named ``<Class>-<identifier>.yaml``. An abstract class
gets no example even when the data has records of it, since the schema says nothing can be
an instance of it.

Run it through ``just gen-examples``; ``just gen-doc`` runs it before gen-doc. With
``--validate`` it also checks each example against its class with linkml's validator, about
half a second a class, and exits 1 when one fails. ``lib/test/test_schema_examples.py``
validates one class in the fast suite and every class in the slow one.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# The justfile runs this file by path, which puts scripts/ rather than the project root on
# sys.path, so the root is added before the project's own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from linkml_runtime.utils.schemaview import SchemaView  # noqa: E402


def example_file(class_name: str, identifier: str) -> str:
    """The file name gen-doc looks for: the class, a hyphen, then the identifier made safe.

    Characters other than letters, digits, dots, hyphens and underscores, such as the colon
    of a CURIE or a slash, become underscores so that the identifier is a valid file name.
    """
    return f"{class_name}-{re.sub(r'[^A-Za-z0-9._-]+', '_', identifier)}.yaml"


def choose_examples(
    view: SchemaView, rows: dict[str, list[dict[str, Any]]]
) -> dict[str, dict[str, Any]]:
    """The example record of each concrete class with records, keyed by class.

    The example is the record whose identifier sorts first, so it changes only when the
    data does. A class without an identifier slot takes its first record as given.
    """
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


def write_examples(
    view: SchemaView, examples: dict[str, dict[str, Any]], directory: Path
) -> list[Path]:
    """Write each example to ``directory``, after removing the YAML files a previous run left."""
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.yaml"):
        stale.unlink()
    paths = []
    for class_name, record in examples.items():
        path = directory / example_file(class_name, identifier_of(view, class_name, record))
        text = yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=100)
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    return paths


def validate_examples(
    view: SchemaView, examples: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    """Validate each example against its class and return the messages, keyed by class.

    The JSON Schema plugin is closed, so a key the class does not have is an error too.
    """
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin

    validator = Validator(view.schema, validation_plugins=[JsonschemaValidationPlugin(closed=True)])
    failures = {}
    for class_name, record in examples.items():
        report = validator.validate(record, class_name)
        if report.results:
            failures[class_name] = [result.message for result in report.results]
    return failures


def main(argv: list[str] | None = None) -> int:
    from lib.api.exposure import schema_view
    from lib.store.loader import load_container, rows_by_class

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="where gen-doc will look for examples")
    parser.add_argument("--validate", action="store_true", help="validate every example")
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    view = schema_view()
    rows = rows_by_class(load_container(byod=False))
    examples = choose_examples(view, rows)
    paths = write_examples(view, examples, args.directory)
    print(f"wrote {len(paths)} examples to {args.directory}")
    skipped = sorted(set(rows) - set(examples))
    if skipped:
        print(f"no example for the abstract classes with records: {', '.join(skipped)}")
    if args.validate:
        failures = validate_examples(view, examples)
        for class_name, messages in sorted(failures.items()):
            for message in messages:
                print(f"{class_name}: {message}", file=sys.stderr)
        print(f"validated {len(examples)} examples, {len(failures)} failed")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
