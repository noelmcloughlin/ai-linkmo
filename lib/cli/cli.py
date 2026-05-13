"""CLI tool for AI-LinkMO demo
- provides command-line interface for API operations."""

import argparse
import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
import yaml
from rich.console import Console
from rich.json import JSON as RichJSON
from rich.panel import Panel
from rich.text import Text

from lib.cli.utils import EnhancedJSONEncoder, detect_server_url, display_error, display_result

__all__ = ['main', 'parse_arguments']

DEFAULT_API_BASE_URL = os.getenv("AI_ATLAS_API_URL", "http://localhost:8000")
OPENAPI_SPEC_PATH = Path(__file__).parent.parent / "api/openapi.yaml"
# Common ports for auto-detecting server (order of preference)
COMMON_PORTS = [8000, 8080, 8888, 5000]
# Parameters to exclude from API/handler calls (internal use only)
EXCLUDED_PARAMS: Set[str] = {'endpoint', 'mode', 'endpoint_map', 'operationid_map', 'scope', 'required_parameters', 'count', 'verbose', 'pretty'}
# Special endpoint handling
ARES_ENDPOINT = '/ares'
ARES_PARAMS: Set[str] = {'risks', 'inference_engine', 'target'}

# Initialize console for rich output
console = Console()
logger = logging.getLogger(__name__)

# Set default logging level to WARNING (suppress INFO logs by default)
logging.basicConfig(level=logging.WARNING, force=True)
# Suppress AIAtlasNexus library logs by setting level and removing handlers
for logger_name in ['ai_atlas_nexus', 'AIAtlasNexus']:
    lib_logger = logging.getLogger(logger_name)
    lib_logger.setLevel(logging.WARNING)
    lib_logger.propagate = False

# ============================================================================
# OPENAPI SPEC LOADING
# ============================================================================

@lru_cache(maxsize=1)
def load_openapi_spec() -> Dict[str, Any]:
    """Load and parse the OpenAPI specification file.
    
    Uses caching to avoid re-parsing the spec on multiple calls.
    
    Returns:
        Parsed OpenAPI specification as dictionary
        
    Raises:
        FileNotFoundError: If OpenAPI spec file not found
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"OpenAPI spec not found at: {OPENAPI_SPEC_PATH}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse OpenAPI spec: {e}")
        raise


def extract_endpoints_from_spec(openapi_spec: Dict[str, Any]) -> tuple[List[str], Dict[str, str], Dict[str, Optional[str]]]:
    """Extract valid scopes, endpoint mappings, and operation IDs from OpenAPI spec.
    
    Args:
        openapi_spec: Parsed OpenAPI specification
        
    Returns:
        Tuple of (valid_scopes, endpoint_map, operationid_map)
    """
    paths = openapi_spec.get('paths', {})
    valid_scopes: List[str] = []
    endpoint_map: Dict[str, str] = {}
    operationid_map: Dict[str, Optional[str]] = {}
    
    for endpoint, methods in paths.items():
        # Add GET endpoints
        if 'get' in methods:
            ep_name = endpoint.strip('/').replace('/', '_') or 'root'
            valid_scopes.append(ep_name)
            endpoint_map[ep_name] = endpoint
            operationid_map[ep_name] = methods['get'].get('operationId')
        
        # Add /ares POST endpoint support
        if endpoint == ARES_ENDPOINT and 'post' in methods:
            ep_name = 'ares'
            if ep_name not in valid_scopes:
                valid_scopes.append(ep_name)
            endpoint_map[ep_name] = endpoint
            operationid_map[ep_name] = methods['post'].get('operationId', 'ares')
    
    return valid_scopes, endpoint_map, operationid_map


def extract_parameters_from_spec(openapi_spec: Dict[str, Any]) -> tuple[
    Dict[str, Dict[str, Any]], 
    Dict[str, Set[str]], 
    Dict[str, Set[str]]
]:
    """Extract parameters from OpenAPI spec, mapping both globally and per-endpoint.
    
    Args:
        openapi_spec: Parsed OpenAPI specification
        
    Returns:
        Tuple of (all_parameters, endpoint_parameters, required_parameters) where:
        - all_parameters: Dict mapping parameter names to their configuration
        - endpoint_parameters: Dict mapping endpoint names to set of parameter names
        - required_parameters: Dict mapping endpoint names to set of required parameter names
    """
    paths = openapi_spec.get('paths', {})
    all_parameters: Dict[str, Dict[str, Any]] = {}
    endpoint_parameters: Dict[str, Set[str]] = {}
    required_parameters: Dict[str, Set[str]] = {}
    
    # Add CLI-specific parameters not in OpenAPI (available to all endpoints)
    all_parameters['verbose'] = {
        'schema': {'type': 'boolean'},
        'description': 'Enable verbose mode to print parsed arguments',
        'required': False
    }
    all_parameters['count'] = {
        'schema': {'type': 'boolean'},
        'description': 'Return only the count of results',
        'required': False
    }
    all_parameters['pretty'] = {
        'schema': {'type': 'boolean'},
        'description': 'Format JSON output with indentation (default: auto-detect based on terminal)',
        'required': False,
    }
    
    for endpoint, methods in paths.items():
        ep_name = endpoint.strip('/').replace('/', '_') or 'root'
        endpoint_parameters[ep_name] = set()
        required_parameters[ep_name] = set()
        
        for method in ['get', 'post', 'put']:
            if method not in methods:
                continue
                
            method_spec = methods[method]
            params = method_spec.get('parameters', [])
            
            for param in params:
                if param.get('in') != 'query':
                    continue
                    
                param_name = param.get('name')
                if not param_name:
                    continue
                
                # Skip 'id' as it's handled separately in positional args
                if param_name == 'id':
                    continue
                
                # Get schema and description from OpenAPI spec
                schema = param.get('schema', {})
                description = param.get('description', '').strip()
                is_required = param.get('required', False)
                
                # Use simple fallback if no description provided
                if not description:
                    description = f'Filter by {param_name}'
                
                # Store unique parameter info
                if param_name not in all_parameters:
                    all_parameters[param_name] = {
                        'schema': schema,
                        'description': description,
                        'required': is_required
                    }
                
                # Map parameter to this endpoint
                endpoint_parameters[ep_name].add(param_name)
                
                # Track required parameters per endpoint
                if is_required:
                    required_parameters[ep_name].add(param_name)
    
    # Add verbose, count, and pretty to all endpoints
    for ep_name in endpoint_parameters:
        endpoint_parameters[ep_name].add('verbose')
        endpoint_parameters[ep_name].add('count')
        endpoint_parameters[ep_name].add('pretty')
    
    return all_parameters, endpoint_parameters, required_parameters


def schema_to_argparse_config(param_name: str, param_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAPI parameter schema to argparse configuration.
    
    Args:
        param_name: Name of the parameter
        param_config: Parameter configuration from OpenAPI
        
    Returns:
        Dictionary with argparse add_argument kwargs
    """
    schema = param_config.get('schema', {})
    schema_type = schema.get('type', 'string')
    description = param_config.get('description', '')
    is_required = param_config.get('required', False)
    param_default = param_config.get('default', argparse.SUPPRESS)
    
    config: Dict[str, Any] = {'help': description}
    
    # Set default if provided
    if param_default != argparse.SUPPRESS:
        config['default'] = param_default
    
    # Add required indicator to help text (but don't enforce in argparse)
    if is_required:
        config['help'] = f"{description} [REQUIRED for some endpoints]"
    
    # Map OpenAPI types to Python/argparse types
    if schema_type == 'integer':
        config['type'] = int
    elif schema_type == 'boolean':
        # Special handling for pretty parameter to support auto-detection
        if param_name == 'pretty':
            config['action'] = 'store_true'
        else:
            config['action'] = 'store_true'
    elif schema_type == 'number':
        config['type'] = float
    else:  # string or default
        config['type'] = str
    
    # Add enum choices if defined in schema
    if 'enum' in schema and schema_type in ('string', 'integer', 'number'):
        enum_values = schema['enum']
        config['choices'] = enum_values
        # Add choices to help text
        choices_str = ', '.join(str(v) for v in enum_values)
        config['help'] = f"{config['help']} (choices: {choices_str})"
    
    return config


# ============================================================================
# PARAMETER VALIDATION
# ============================================================================

def validate_required_parameters(
    args: argparse.Namespace,
    scope: str,
    required_params: Dict[str, Set[str]]
) -> List[str]:
    """Validate that all required parameters for the scope are provided.
    
    Args:
        args: Parsed arguments namespace
        scope: Selected scope/endpoint
        required_params: Dict mapping scopes to their required parameters
        
    Returns:
        List of missing required parameter names (empty if all provided)
    """
    if scope not in required_params:
        return []
    
    missing_params = []
    for param in required_params[scope]:
        value = getattr(args, param, None)
        if value is None:
            missing_params.append(param)
    
    return missing_params


# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def create_argument_parser(
    valid_scopes: List[str], 
    mode: str, 
    openapi_spec: Dict[str, Any]
) -> argparse.ArgumentParser:
    """Create and configure the argument parser.
    
    Args:
        valid_scopes: List of valid scope names
        mode: Operating mode ('api' or 'local')
        openapi_spec: OpenAPI specification for dynamic parameter extraction
        
    Returns:
        Configured ArgumentParser instance
    """
    # Create examples section for epilog
    examples = '''
Examples:
  List all taxonomies:
    ./ai taxonomy

  Get specific risk by ID:
    ./ai risk atlas-toxic-output

  Count risks from a taxonomy:
    ./ai risk --isDefinedByTaxonomy nist-ai-rmf --count

  Filter actions by phase:
    ./ai action --phase training-tuning --count

  Get related risks:
    ./ai risk atlas-toxic-output --related

  Use BYOD (Bring Your Own Data):
    ./ai taxonomy --byod

  API mode (fast, default):
    ./ai risk --count --mode=api

  Local mode (slower):
    ./ai risk --count --mode=local
'''
    
    parser = argparse.ArgumentParser(
        prog='./ai',
        description="""AI-LinkMO CLI Demo - Query AI risk taxonomies, controls, and related entities.

Use API mode (default) for fast queries, or local mode for offline operation.""",
        usage="./ai <scope> [id] [--options]",
        epilog=examples,
        formatter_class=argparse.RawTextHelpFormatter,  # Preserves newlines in all help text
        allow_abbrev=False  # Disable prefix matching to avoid --part matching --partof
    )
    
    # Mode selection
    parser.add_argument(
        '--mode',
        choices=['api', 'local'],
        default=mode,
        metavar='MODE',
        help='execution mode: "api" (fast, requires server) or "local" (slow, offline)'
    )
    
    # Scope argument - simple listing with newlines every 5 scopes
    # RawTextHelpFormatter preserves these newlines exactly
    scopes_per_line = 5
    scope_lines = []
    for i in range(0, len(valid_scopes), scopes_per_line):
        line_scopes = valid_scopes[i:i+scopes_per_line]
        scope_lines.append(", ".join(line_scopes))
    
    # Use newlines between groups
    scope_help = "\n".join(scope_lines)
    
    parser.add_argument(
        "scope",
        type=str,
        choices=valid_scopes,
        metavar="scope",
        help=scope_help
    )
    
    # ID argument
    parser.add_argument(
        "id",
        type=str,
        nargs="?",
        default=None,
        metavar="id",
        help="Optional: specific ID to query (omit to list all items in scope)"
    )
    
    # Extract parameters dynamically from OpenAPI spec
    all_parameters, _, _ = extract_parameters_from_spec(openapi_spec)
    filter_group = parser.add_argument_group(
        "Filter Options",
        "Filter results by various criteria (use --help with a specific scope for relevant filters)"
    )
    output_group = parser.add_argument_group(
        "Output Options",
        "Control output format and verbosity"
    )
    output_params = {'verbose', 'count', 'pretty', 'export'}
    special_params = {'byod', 'filename', 'engine'}
    
    # Sort parameters alphabetically and assign to appropriate groups
    for param_name in sorted(all_parameters.keys()):
        param_config = all_parameters[param_name]
        arg_config = schema_to_argparse_config(param_name, param_config)
        arg_flag = f"--{param_name}"
        
        # Assign to appropriate group
        if param_name in output_params:
            output_group.add_argument(arg_flag, **arg_config)
        elif param_name in special_params:
            parser.add_argument(arg_flag, **arg_config)
        else:
            filter_group.add_argument(arg_flag, **arg_config)
    
    return parser


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the AI-LinkMO CLI Demo.

    Returns:
        Parsed arguments namespace with endpoint mappings and validation data
        
    Raises:
        SystemExit: If argument parsing fails or help is requested
    """
    # Load OpenAPI specification
    openapi_spec = load_openapi_spec()
    valid_scopes, endpoint_map, operationid_map = extract_endpoints_from_spec(openapi_spec)
    _, _, required_parameters = extract_parameters_from_spec(openapi_spec)
    
    # Create and parse arguments with standard argparse
    parser = create_argument_parser(valid_scopes, 'api', openapi_spec)
    args = parser.parse_args()
    
    # Attach endpoint mappings and validation data to args
    args.endpoint_map = endpoint_map
    args.operationid_map = operationid_map
    args.required_parameters = required_parameters
    
    # Validate required parameters
    missing_params = validate_required_parameters(args, args.scope, required_parameters)
    if missing_params:
        missing_list = ', '.join(f'--{p}' for p in missing_params)
        display_error(
            "Missing Required Parameters",
            f"The following required parameters are missing for '{args.scope}': {missing_list}"
        )
        raise SystemExit(2)
    
    # Verbose output if requested
    if getattr(args, 'verbose', False):
        console.print("\n[bold cyan][Parsed Arguments][/bold cyan]")
        for arg, value in vars(args).items():
            if arg not in ('endpoint_map', 'operationid_map', 'required_parameters'):
                console.print(f"  {arg}: {value}")
    
    return args

# ============================================================================
# API CLIENT (Fast CLI compared to local mode)
# ============================================================================


def call_api_server(endpoint: str, args_dict: Dict[str, Any], base_url: str = DEFAULT_API_BASE_URL) -> None:
    """Call the API server with the given endpoint and parameters.
    
    Auto-detects server port if connection fails on default URL.
    
    Args:
        endpoint: API endpoint to call
        args_dict: Dictionary of arguments/parameters
        base_url: Base URL of the API server
        
    Raises:
        requests.exceptions.RequestException: If API call fails
    """
    verbose = args_dict.get('verbose', False)
    show_count_only = args_dict.get('count', False)
    # Auto-detect pretty printing: use if explicitly set, or if outputting to interactive terminal.
    # os.isatty(1) checks the raw stdout file descriptor, more reliable than sys.stdout.isatty()
    # when spawned via uv run or similar process managers.
    _is_tty = os.isatty(1) if hasattr(os, 'isatty') else sys.stdout.isatty()
    show_pretty = bool(args_dict.get('pretty')) or (not show_count_only and _is_tty)
    
    # Try to detect server URL (uses cache if available)
    detected_url = detect_server_url(base_url, COMMON_PORTS)
    if detected_url:
        url = detected_url + endpoint
        if verbose and detected_url != base_url:
            console.print(f"[dim]Using server at {detected_url}[/dim]")
    else:
        url = base_url + endpoint
    
    try:
        # Filter out internal CLI parameters and boolean False values (argparse defaults)
        filtered_args = {
            k: v for k, v in args_dict.items()
            if v is not None 
            and k not in EXCLUDED_PARAMS
            and not (isinstance(v, bool) and v is False)  # Exclude False booleans (not provided by user)
        }
        
        if endpoint == ARES_ENDPOINT:
            response = requests.post(url, json=filtered_args, timeout=30)
        else:
            response = requests.get(url, params=filtered_args, timeout=30)
        
        response.raise_for_status()
        
        # If count flag is set, only show the count value
        if show_count_only:
            try:
                result = json.loads(response.text)
                if isinstance(result, dict) and 'count' in result:
                    print(result['count'])
                else:
                    print(response.text)
            except json.JSONDecodeError:
                print(response.text)
        elif show_pretty:
            # Pretty print the JSON with Rich syntax highlighting
            try:
                json.loads(response.text)  # validate
                console.print(RichJSON(response.text))
            except json.JSONDecodeError:
                print(response.text)
        else:
            # Use print() instead of console.print() to avoid Rich's line wrapping
            # which can corrupt JSON output
            print(response.text)
        
    except requests.exceptions.Timeout:
        display_error("Timeout Error", "Request timed out. Please check if the server is running.")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        # Try to provide helpful error message with attempted URLs
        tried_urls = [base_url] + [f"http://localhost:{p}" for p in COMMON_PORTS if f"http://localhost:{p}" != base_url]
        attempted = ", ".join(set(tried_urls[:4]))  # Show first 4 unique URLs
        display_error(
            "Connection Error", 
            f"Could not connect to API server.\nTried: {attempted}\n\nIs the server running? Start it with: uv run uvicorn lib.api.server:app --reload"
        )
        sys.exit(1)
    except requests.exceptions.HTTPError:
        display_error("HTTP Error", f"HTTP {response.status_code}: {response.text}")
        sys.exit(1)
    except Exception as e:
        display_error("Error", f"Unexpected error: {str(e)}")
        sys.exit(1)

# ============================================================================
# LOCAL MODE HANDLER (much slower than FastAPI but avoids API server overhead)
# ============================================================================

def call_local_handler(endpoint: str, args_dict: Dict[str, Any]) -> None:
    """Call local handler functions directly without going through API.
    
    Args:
        endpoint: Endpoint to call
        args_dict: Dictionary of arguments
    """
    from fastapi import HTTPException
    
    operationid_map = args_dict.get('operationid_map', {})
    endpoint_key = args_dict.get('scope')
    operation_id = operationid_map.get(endpoint_key)
    
    if not operation_id:
        display_error("Configuration Error", f"No operationId found for endpoint '{endpoint_key}'")
        return
    
    # Parse operation_id to get function name
    parts = operation_id.split('.')
    func_name = parts[1] if len(parts) == 2 else operation_id
    
    # Suppress logging before importing heavier modules
    verbose = args_dict.get('verbose', False)
    if not verbose:
        # Set root logger and all existing loggers to CRITICAL before imports
        logging.getLogger().setLevel(logging.CRITICAL)
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    
    try:
        # Import handler module and get function (after log suppression)
        import importlib
        import inspect
        
        handlers = importlib.import_module('lib.api.handlers')
        
        func = getattr(handlers, func_name)
        
        # Filter arguments based on function signature, excluding internal params and False booleans
        sig = inspect.signature(func)
        accepted_args = set(sig.parameters)
        filtered_call_args = {
            k: v for k, v in args_dict.items()
            if v is not None 
            and k in accepted_args 
            and k not in EXCLUDED_PARAMS
            and not (isinstance(v, bool) and v is False)  # Exclude False booleans (not provided by user)
        }
        
        # Call handler function
        try:
            result = func(**filtered_call_args)
        except HTTPException as e:
            display_error("API Error", f"[{e.status_code}] {e.detail}")
            return
        
        # Display results with rich formatting
        show_count_only = args_dict.get('count', False)
        # Auto-detect pretty printing: use if explicitly set, or if outputting to interactive terminal.
        # os.isatty(1) checks the raw stdout file descriptor, more reliable than sys.stdout.isatty()
        # when spawned via uv run or similar process managers.
        _is_tty = os.isatty(1) if hasattr(os, 'isatty') else sys.stdout.isatty()
        show_pretty = bool(args_dict.get('pretty')) or (not show_count_only and _is_tty)
        display_result(result, count_only=show_count_only, pretty=show_pretty)
        
    except ModuleNotFoundError as e:
        display_error("Import Error", f"Handler module not found: {e}")
    except AttributeError:
        display_error("Not Implemented", f"Handler for operationId '{operation_id}' not implemented")
    except Exception as e:
        display_error("Error", f"Unexpected error: {str(e)}")
        logger.exception("Error in local handler")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Main entry point for the CLI application."""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Configure logging level based on verbose mode
        verbose = getattr(args, 'verbose', False)
        if verbose:
            # Enable INFO logs when in verbose mode
            logging.getLogger().setLevel(logging.INFO)
            for logger_name in ['ai_atlas_nexus', 'AIAtlasNexus']:
                lib_logger = logging.getLogger(logger_name)
                lib_logger.setLevel(logging.INFO)
                lib_logger.propagate = True
        
        # Extract endpoint and parameters
        endpoint_map = args.endpoint_map
        operationid_map = args.operationid_map
        endpoint = endpoint_map[args.scope]
        args_dict = vars(args)
        args_dict['operationid_map'] = operationid_map
        
        # Display operation info (only in verbose mode)
        if verbose:
            operation_id = operationid_map.get(args.scope, 'N/A')
            console.print(f"[bold cyan][Operation ID: {operation_id}][/bold cyan]")
            console.print(f"[bold cyan][Mode: {args.mode}][/bold cyan]")
        
        # Call appropriate handler
        if args.mode == 'api':
            call_api_server(endpoint, args_dict)
        else:
            call_local_handler(endpoint, args_dict)
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        display_error("Error", f"Fatal error: {str(e)}")
        if getattr(args, 'verbose', False):
            logger.exception("Fatal error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
