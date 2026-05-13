"""
Handler constants for API endpoints.

This module contains shared constants used across handler functions.

Parameter Naming Strategy:
- CLI and API use the same OpenAPI parameter names directly (no translation layer)
- Example: --isDefinedByTaxonomy, --hasDocumentation, --isPartOf
- This ensures consistency across CLI, API, and documentation

API parameter naming convention:
- Relationships: has*, is*, belongs*, etc. (e.g., isDefinedByTaxonomy, hasDocumentation)
- Special cases: type, phase, descriptor, provider (lowercase, no prefix)
"""

import os
from pathlib import Path
from typing import Set

# ============================================================================
# CLI CONFIGURATION CONSTANTS
# ============================================================================

# Default API base URL (can be overridden via AI_ATLAS_API_URL environment variable)
DEFAULT_API_BASE_URL = os.getenv("AI_ATLAS_API_URL", "http://localhost:8000")

# Path to OpenAPI specification file
OPENAPI_SPEC_PATH = Path(__file__).parent / "openapi.yaml"

# Common ports for auto-detecting API server (in order of preference)
COMMON_PORTS = [8000, 8080, 8888, 5000]

# Special endpoint handling for ARES (AI Risk Evaluation Service)
ARES_ENDPOINT = '/ares'
ARES_PARAMS: Set[str] = {'risks', 'inference_engine', 'target'}

# ============================================================================
# EXCLUDED PARAMETERS
# ============================================================================

# Parameters to exclude from API/handler calls (internal CLI use only)
# These parameters control CLI behavior and output formatting, not backend queries
EXCLUDED_PARAMS = {
    'endpoint',          # Internal routing metadata
    'mode',              # CLI mode selection (api vs local)
    'endpoint_map',      # Internal routing dictionary
    'operationid_map',   # Internal operation ID mapping
    'scope',             # CLI scope argument (converted to endpoint)
    'required_parameters',  # Internal validation metadata
    'count',             # CLI display flag: show only count
    'verbose',           # CLI display flag: verbose output
    'pretty',            # CLI display flag: pretty-print JSON
}
