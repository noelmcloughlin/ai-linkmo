"""The class examples come from the data, validate against their classes, and gen-doc shows them.

``scripts/gen_examples.py`` writes the examples that ``just gen-doc`` passes to gen-doc as
``--example-directory``. The fast tests check the choice and the file names, validate one
example, and ask gen-doc's own lookup which files it finds for a class, which is what its
class template calls. The slow tests validate every example, about fifteen seconds, and
render the whole schema with gen-doc, about five.
"""

from __future__ import annotations

import pytest
import yaml

from lib.api.exposure import schema_directory, schema_view
from scripts.gen_examples import (
    choose_examples,
    example_file,
    identifier_of,
    validate_examples,
    write_examples,
)


@pytest.fixture(scope="module")
def rows():
    from lib.store.loader import load_container, rows_by_class

    return rows_by_class(load_container(byod=False))


@pytest.fixture(scope="module")
def examples(rows):
    return choose_examples(schema_view(), rows)


@pytest.fixture(scope="module")
def example_dir(tmp_path_factory, examples):
    directory = tmp_path_factory.mktemp("examples")
    write_examples(schema_view(), examples, directory)
    return directory


def test_example_files_are_named_as_gen_doc_expects():
    assert example_file("Risk", "atlas-toxic-output") == "Risk-atlas-toxic-output.yaml"
    # A CURIE's colon and a path's slash are not safe in a file name.
    assert example_file("Dataset", "hf:org/name") == "Dataset-hf_org_name.yaml"


def test_each_concrete_class_with_records_has_its_first_record(rows, examples):
    view = schema_view()
    concrete = {name for name in rows if not view.get_class(name).abstract}
    assert set(examples) == concrete
    for class_name, record in examples.items():
        key = view.get_identifier_slot(class_name).name
        assert record[key] == min(str(r[key]) for r in rows[class_name]), class_name


def test_written_examples_read_back_as_the_records(examples, example_dir):
    view = schema_view()
    files = sorted(path.name for path in example_dir.glob("*.yaml"))
    assert len(files) == len(examples)
    record = examples["Risk"]
    path = example_dir / example_file("Risk", identifier_of(view, "Risk", record))
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == record


def test_an_example_validates_against_its_class_and_a_bad_one_does_not(examples):
    view = schema_view()
    risk = examples["Risk"]
    assert validate_examples(view, {"Risk": risk}) == {}
    # The validator is closed, so a key the class does not have is reported.
    failures = validate_examples(view, {"Risk": {**risk, "notASlot": "x"}})
    assert "Risk" in failures and any("notASlot" in m for m in failures["Risk"])


def test_gen_doc_finds_exactly_the_class_example(examples, example_dir):
    from linkml.generators.docgen import DocGenerator

    generator = DocGenerator(
        str(schema_directory() / "ai-risk-ontology.yaml"),
        example_directory=str(example_dir),
        render_imports=True,
    )
    view = schema_view()
    for class_name in ("Risk", "RiskGroup"):
        stem = example_file(class_name, identifier_of(view, class_name, examples[class_name]))
        # The lookup is by name prefix, so Risk must not pick up RiskGroup's file.
        assert [name for name, _ in generator.example_object_blobs(class_name)] == [stem[:-5]]


@pytest.mark.slow
def test_every_example_validates_against_its_class(examples):
    assert validate_examples(schema_view(), examples) == {}


@pytest.mark.slow
def test_gen_doc_renders_each_example_on_its_class_page(examples, example_dir, tmp_path):
    from linkml.generators.docgen import DocGenerator

    DocGenerator(
        str(schema_directory() / "ai-risk-ontology.yaml"),
        directory=str(tmp_path),
        example_directory=str(example_dir),
        render_imports=True,
    ).serialize()
    view = schema_view()
    for class_name, record in examples.items():
        page = (tmp_path / f"{class_name}.md").read_text(encoding="utf-8")
        stem = example_file(class_name, identifier_of(view, class_name, record))[:-5]
        assert "## Examples" in page and f"### Example: {stem}" in page, class_name
    risk = (tmp_path / "Risk.md").read_text(encoding="utf-8")
    assert f"name: {examples['Risk']['name']}" in risk
