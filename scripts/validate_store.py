"""Validate the DuckDB store against the ontology schema and report what linkml-store finds.

linkml-store's own ``validate`` command exits 0 whether or not it found anything, and run
without a config it validates nothing at all, so its exit code says nothing; its agent skill
warns of the same. This script runs the same validation through the Python API, where no
stdout noise can mix with the result (linkml/linkml-store#65), reads the findings, prints
one line per finding and a summary, writes them as JSON when asked, and exits 1 when there
are more than ``--allow`` permits.

linkml-store 0.3.2 makes two passes. Each row is checked against its class with a closed
JSON Schema, so an unknown key, a value outside an enum or a missing required slot is a
finding. Then every single-valued reference to a class the store holds is looked up in the
collections typed exactly as the slot's range and reported when absent. That second pass
has two gaps this script has to live with. List-valued references are not checked at all,
so a ``hasRelatedAction`` id that points nowhere passes. And the lookup ignores the class
hierarchy: the store keeps one collection per concrete class, so a ``Taxonomy``-ranged
value that names a ``RiskTaxonomy`` row reads as missing. Those findings are looked up
again here in the collections of the range's subclasses, dropped when found there, and
counted in the summary so that nothing disappears silently.

Per finding, ``collection`` is the collection the finding concerns: the row's own
collection for a JSON Schema finding, the collection the reference was looked up in for a
referential one. Run it through ``just validate-store``. CI runs it with ``--allow`` set
to the number of findings upstream's data produces today; that number is data debt and
must only go down.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

# The justfile runs this file by path, which puts scripts/ rather than the project root on
# sys.path, so the root is added before the project's own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REFERENTIAL = "ReferentialIntegrity"


@dataclass(frozen=True, order=True)
class Finding:
    """One validation result, flattened to what a reader needs to find and fix the row."""

    database: str
    collection: str
    severity: str
    type: str
    instance: str
    message: str
    instantiates: str

    def line(self) -> str:
        message = " ".join(self.message.split())
        return f"{self.database} {self.collection} {self.severity} {self.type} {self.instance} {message}"


@dataclass
class Report:
    """The findings of a run, and per database how many referential ones were resolved."""

    findings: list[Finding] = field(default_factory=list)
    resolved: dict[str, int] = field(default_factory=dict)

    def summary(self) -> list[str]:
        """One line per database with its count by finding type, in alias order."""
        by_database: dict[str, Counter] = {alias: Counter() for alias in self.resolved}
        for finding in self.findings:
            by_database.setdefault(finding.database, Counter())[finding.type] += 1
        lines = []
        for alias, counts in sorted(by_database.items()):
            detail = (
                ", ".join(f"{kind} {count}" for kind, count in sorted(counts.items()))
                or "none"
            )
            line = f"{alias}: {sum(counts.values())} findings ({detail})"
            if self.resolved.get(alias):
                line += f"; {self.resolved[alias]} referential findings resolved in subclass collections"
            lines.append(line)
        return lines


def load_client_config(config_path: Path) -> dict[str, Any]:
    """The linkml-store client config, reduced to the keys its model accepts.

    linkml-store's config model forbids keys it does not know. The loader keeps its
    provenance in a comment for that reason, but a key added by hand would still make the
    whole file unreadable, so anything the model does not declare is dropped here.
    """
    from linkml_store.api.config import ClientConfig

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return {
        key: value for key, value in raw.items() if key in ClientConfig.model_fields
    }


def attach(config: dict[str, Any], alias: str, base_dir: Path):
    """Attach one database of the config with a schema view its collections can use.

    ``Client.from_config`` loads the schema named by ``schema_location`` and declares the
    collections with their classes. Should a collection still lack a class definition, the
    view is replaced by the project's merged view of the same schema.
    """
    from linkml_store import Client

    client = Client().from_config(config, base_dir=str(base_dir))
    database = client.get_database(alias)
    if any(
        collection.class_definition() is None
        for collection in database.list_collections()
    ):
        from lib.api.exposure import schema_view

        database.set_schema_view(schema_view())
    return database


def finding_from_result(
    database: str, result, alias_by_class: dict[str, str]
) -> Finding:
    """Flatten a linkml-store ``ValidationResult``.

    A JSON Schema result carries the whole row as ``instance`` and the class it was
    validated as in ``instantiates``; a referential one carries the missing id and the class
    it was looked for. Both are reduced to an id and the collection holding that class.
    """
    instance = result.instance
    if isinstance(instance, dict):
        instance = instance.get("id", json.dumps(instance, sort_keys=True, default=str))
    severity = getattr(result.severity, "value", str(result.severity))
    class_name = result.instantiates or ""
    return Finding(
        database=database,
        collection=alias_by_class.get(class_name, class_name),
        severity=severity,
        type=result.type,
        instance=str(instance),
        message=result.message,
        instantiates=class_name,
    )


def resolve_in_subclass_collections(
    database, findings: list[Finding]
) -> tuple[list[Finding], int]:
    """Drop the referential findings whose id exists in a collection of a subclass of the range.

    Each distinct id is looked up once per subclass collection with the same ``get_one``
    linkml-store used, so the result is what its check would give if it knew the hierarchy.
    Returns the findings kept and the number dropped.
    """
    view = database.schema_view
    by_class = {
        collection.target_class_name: collection
        for collection in database.list_collections()
    }
    seen: dict[tuple[str, str], bool] = {}

    def exists(class_name: str, identifier: str) -> bool:
        key = (class_name, identifier)
        if key not in seen:
            seen[key] = by_class[class_name].get_one(identifier) is not None
        return seen[key]

    kept: list[Finding] = []
    resolved = 0
    for finding in findings:
        if finding.type == REFERENTIAL:
            subclasses = [
                name
                for name in view.class_descendants(finding.instantiates)
                if name != finding.instantiates and name in by_class
            ]
            if any(exists(name, finding.instance) for name in subclasses):
                resolved += 1
                continue
        kept.append(finding)
    return kept, resolved


def validate_database(database, alias: str) -> tuple[list[Finding], int]:
    """Every finding of one attached database, both passes, in a deterministic order."""
    alias_by_class = {c.target_class_name: c.alias for c in database.list_collections()}
    results = database.iter_validate_database(ensure_referential_integrity=True)
    findings = [
        finding_from_result(alias, result, alias_by_class) for result in results
    ]
    kept, resolved = resolve_in_subclass_collections(database, findings)
    return sorted(kept), resolved


def validate_config(config_path: Path, only: str | None = None) -> Report:
    """Validate every database the config declares, or the one named by ``only``.

    Each database is closed after its pass. DuckDB allows one open instance per file in a
    process, so a caller that opens the same file next, as the tests do, needs this.
    """
    config_path = Path(config_path)
    config = load_client_config(config_path)
    aliases = sorted(config.get("databases", {}))
    if only is not None:
        if only not in aliases:
            raise SystemExit(
                f"{config_path} declares no database {only!r}; it has {', '.join(aliases)}"
            )
        aliases = [only]
    report = Report()
    for alias in aliases:
        started = time.time()
        database = attach(config, alias, config_path.parent)
        try:
            findings, resolved = validate_database(database, alias)
        finally:
            database.close()
        report.findings.extend(findings)
        report.resolved[alias] = resolved
        print(f"validated {alias} in {time.time() - started:.1f} s", file=sys.stderr)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "config", type=Path, help="the linkml-store config `just load-store` writes"
    )
    parser.add_argument("--database", help="validate only this database of the config")
    parser.add_argument(
        "--output", type=Path, help="write the findings to this file as a JSON list"
    )
    parser.add_argument(
        "--allow",
        type=int,
        default=0,
        help="exit 0 with up to this many findings, 1 with more (default 0)",
    )
    args = parser.parse_args(argv)
    report = validate_config(args.config, args.database)
    for finding in report.findings:
        print(finding.line())
    for line in report.summary():
        print(line)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                [asdict(finding) for finding in report.findings],
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.output}")
    print(f"total {len(report.findings)} findings, allowed {args.allow}")
    return 1 if len(report.findings) > args.allow else 0


if __name__ == "__main__":
    sys.exit(main())
