"""Generate the sidecar's Python datamodel when the project's datamodel is there.

The linkmo template runs this once, at the end of its first copy, with --if-missing. When
`ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology` points into the sidecar's src/, it writes what the sidecar's own
`just gen-python` writes: the pydantic module the project imports, and the dataclasses
module that the sidecar's datamodel package imports beside it. With --if-missing it
writes only the files that do not exist. It never installs anything, and it changes
nothing when the datamodel is in an installed package.

The generators, gen-pydantic and gen-python from the linkml package, are looked for in:

1. the folder named by LINKMO_LINKML_BIN, such as another environment's bin/;
2. the sidecar's own environment, .linkml/.venv, which its `just install` makes;
3. the PATH.

With none of them, it says what to run and stops without failing the copy. Run it again
at any time with `just gen-datamodel`, which replaces both files.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOST_ROOT = Path(__file__).resolve().parents[2]
SIDECAR = HOST_ROOT / ".linkml"
SCHEMA = "pkg:ai_atlas_nexus/ai_risk_ontology/schema/ai-risk-ontology.yaml"
MODULE = "ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology"
SLUG = "ai-risk-ontology"


def outputs() -> list[tuple[str, Path]]:
    """The generator and the file of each module to write, or nothing outside the sidecar."""
    package = MODULE.split(".", 1)[0]
    if not (SIDECAR / "src" / package).is_dir():
        return []
    pydantic_file = SIDECAR / "src" / Path(*MODULE.split(".")).with_suffix(".py")
    return [
        ("gen-pydantic", pydantic_file),
        ("gen-python", pydantic_file.parent / f"{SLUG}.py"),
    ]


def find(generator: str) -> str | None:
    folders = [os.environ.get("LINKMO_LINKML_BIN", ""), str(SIDECAR / ".venv" / "bin"), str(SIDECAR / ".venv" / "Scripts")]
    for folder in filter(None, folders):
        for name in (generator, f"{generator}.exe"):
            candidate = Path(folder) / name
            if candidate.is_file():
                return str(candidate)
    return shutil.which(generator)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--if-missing", action="store_true", help="write only the files that do not exist")
    args = parser.parse_args(argv)
    lenient = 0 if args.if_missing else 1
    wanted = outputs()
    if not wanted:
        print(f"gen-datamodel: {MODULE} is not in the sidecar; nothing to generate")
        return 0
    if args.if_missing:
        wanted = [(generator, target) for generator, target in wanted if not target.is_file()]
        if not wanted:
            print("gen-datamodel: the datamodel exists; left as it is")
            return 0
    schema = HOST_ROOT / SCHEMA
    if not schema.is_file():
        print(f"gen-datamodel: the schema {SCHEMA} does not exist yet; run `just gen-datamodel` once it does")
        return lenient
    for generator, target in wanted:
        command = find(generator)
        if command is None:
            print(
                f"gen-datamodel: {generator} not found. Run `just --justfile .linkml/justfile "
                "install` for the sidecar's environment, or set LINKMO_LINKML_BIN, then `just gen-datamodel`."
            )
            return lenient
        result = subprocess.run([command, str(schema)], capture_output=True, text=True)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)
            print(f"gen-datamodel: {generator} failed with exit code {result.returncode}")
            return lenient and result.returncode
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.stdout, encoding="utf-8")
        print(f"gen-datamodel: wrote {target.relative_to(HOST_ROOT)} with {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
