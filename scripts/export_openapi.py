"""Write the API contract to a file without running a server.

FastAPI builds the OpenAPI document from the registered routes, and the routes are
registered from the exposure file and the schema, so the document can be produced here the
same way the running server produces it at ``/openapi.json``. The committed copy under
``docs/`` lets a reader or a client generator see the contract without starting anything,
and ``lib/test/test_contract_published.py`` fails when it falls behind.

Run it through ``just gen-openapi``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The script is run by path from the justfile, which puts scripts/ rather than the project
# root on sys.path, so the root is added here before the project's own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build_contract() -> dict:
    """The OpenAPI document of the app with every endpoint registered.

    The endpoints are registered directly rather than through the lifespan, so that no
    ``AIAtlasNexus`` instance is created: the contract needs the schema, not the data.
    """
    from lib.api.server import app
    from lib.api.server_kernel import register_class_endpoints, register_hand_endpoints

    register_class_endpoints(app)
    register_hand_endpoints(app)
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
