"""Write the API's contract to a file without running a server.

FastAPI builds the OpenAPI document from the registered routes, and the routes come from
the exposure file and the schema, so the document can be made here exactly as the running
server makes it at /openapi.json. The committed copy lets a reader or a client generator
see the contract without starting anything, and tests/test_published.py fails when it
is out of date. Run it with `just gen-openapi`.

When LinkML's gen-openapi gains a console script, and the fixes that let it describe list
responses and enums without values, the same recipe can publish its output instead.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def build_contract() -> dict:
    """The OpenAPI document, built from the schema alone. No record is read."""
    from ai_risk_ontology_linkmo.server import app

    return app.openapi()


def render(contract: dict) -> str:
    return json.dumps(contract, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    output = Path(args[0]) if args else Path("docs/openapi.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(build_contract()), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
