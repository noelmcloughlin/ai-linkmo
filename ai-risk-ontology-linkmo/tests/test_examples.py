"""The class examples come from the data, validate against their classes, and gen-doc finds them.

Skipped until the docs dependency group, linkml, is installed.
"""

from __future__ import annotations

import pytest
import yaml

pytest.importorskip("linkml", reason="the docs dependency group is not installed")

from ai_risk_ontology_linkmo.examples import (  # noqa: E402
    choose_examples,
    example_file,
    identifier_of,
    validate_examples,
    write_examples,
)
from ai_risk_ontology_linkmo.schema import schema_view  # noqa: E402
from ai_risk_ontology_linkmo.settings import schema_path  # noqa: E402
from ai_risk_ontology_linkmo.sources import rows_by_class  # noqa: E402


@pytest.fixture(scope="module")
def rows():
    return rows_by_class()


@pytest.fixture(scope="module")
def examples(rows):
    return choose_examples(schema_view(), rows)


@pytest.fixture(scope="module")
def example_dir(tmp_path_factory, examples):
    directory = tmp_path_factory.mktemp("examples")
    write_examples(schema_view(), examples, directory)
    return directory


def test_example_files_are_named_as_gen_doc_expects():
    assert example_file("Thing", "hf:org/name") == "Thing-hf_org_name.yaml"


def test_each_concrete_class_with_records_has_its_first_record(rows, examples):
    view = schema_view()
    assert set(examples) == {name for name in rows if not view.get_class(name).abstract}
    for class_name, record in examples.items():
        key = view.get_identifier_slot(class_name)
        if key is not None:
            assert record[key.name] == min(str(r[key.name]) for r in rows[class_name]), class_name


def test_written_examples_read_back_as_the_records(examples, example_dir):
    view = schema_view()
    assert len(list(example_dir.glob("*.yaml"))) == len(examples)
    for class_name, record in examples.items():
        path = example_dir / example_file(class_name, identifier_of(view, class_name, record))
        assert yaml.safe_load(path.read_text(encoding="utf-8")) == record


def test_every_example_validates_against_its_class(examples):
    assert validate_examples(schema_view(), examples) == {}


def test_gen_doc_finds_exactly_the_class_example(examples, example_dir):
    from linkml.generators.docgen import DocGenerator

    generator = DocGenerator(str(schema_path()), example_directory=str(example_dir), render_imports=True)
    view = schema_view()
    for class_name, record in examples.items():
        stem = example_file(class_name, identifier_of(view, class_name, record))[:-5]
        # The lookup is by name prefix, so a class must not pick up a longer class's file.
        assert [name for name, _ in generator.example_object_blobs(class_name)] == [stem], class_name
