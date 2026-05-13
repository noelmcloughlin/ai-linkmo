# CLI Architecture - OpenAPI as Single Source of Truth

## Overview

This demo CLI provides command-line access to AI-LinkMO.

The OpenAPI specification (`lib/api/openapi.yaml`) is the **single source of truth** for all endpoints and parameters, used by CLI (`lib/cli`) and API (`lib/api`) for consistency and maintainability.

```ascii

lib/cli/
├── cli.py              # Main CLI tool (dynamically reads OpenAPI)
├── utils.py            # Helper utilities
└── README.md           # This file
```

CLI parameter metadata is extracted (`extract_parameters_from_spec()`) from the OpenAPI specification for consistency across both API and CLI.

The schema is converted to argparse format (`schema_to_argparse_config()`) perserving parameter names and descriptions, and the argparse configuration is dynamically created (`create_argument_parser()`).

Parameters added, removed, or modified in `lib/api/openapi.yaml` are automatically handled by the CLI.

## Usage

```bash
# CLI automatically reads from OpenAPI spec
./ai risk --taxonomy nist-ai-rmf

# View all available parameters (from OpenAPI)
./ai --help

# Verbose mode shows all parsed parameters
./ai risk --verbose

# Show only parameters relevant to 'risk' endpoint
./ai risk --help

# Show only parameters relevant to 'model' endpoint  
./ai model --help

# Show all parameters from all endpoints
./ai --help
```

**Validation:**
Validate all handlers match OpenAPI spec:

```bash
uv run python lib/test/validate_handlers.py
uv run python lib/test/validate_handlers.py --strict
uv run python lib/test/validate_handlers.py --verbose
```
