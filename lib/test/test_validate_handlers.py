"""Pytest shim around lib/test/validate_handlers.py.

The standalone script keeps its CLI ergonomics for ad-hoc runs; this shim
lets ``pytest`` auto-discover the same validation so handler signatures and
OpenAPI stay in lock-step in CI.
"""

import importlib.util
from pathlib import Path

_VALIDATOR_PATH = Path(__file__).resolve().parent / "validate_handlers.py"
_spec = importlib.util.spec_from_file_location(
    "lib_test_validate_handlers", _VALIDATOR_PATH
)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
assert _spec and _spec.loader  # for type-checkers
_spec.loader.exec_module(_module)  # type: ignore[union-attr]

test_handlers_match_openapi = _module.test_handlers_match_openapi
