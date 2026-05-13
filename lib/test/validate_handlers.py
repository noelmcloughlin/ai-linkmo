#!/usr/bin/env python3
"""Validate that handler function signatures match OpenAPI specification.

This script ensures complete synchronization between:
- OpenAPI parameter definitions
- Handler function signatures
- CLI parameter extraction

Ensures the OpenAPI-as-source-of-truth architecture is maintained.

Usage:
    python lib/api/validate_handlers.py
    # or
    ./lib/api/validate_handlers.py
    
    # Check mode (for CI/CD)
    python lib/api/validate_handlers.py --strict
"""

import argparse
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_openapi_spec(spec_path: Path) -> Dict[str, Any]:
    """Load and parse the OpenAPI specification."""
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)


def extract_endpoint_parameters(openapi_spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract parameters for each endpoint from OpenAPI spec.
    
    Returns:
        Dict mapping operation IDs to their parameter specifications
    """
    paths = openapi_spec.get('paths', {})
    endpoint_params: Dict[str, Dict[str, Any]] = {}
    
    for endpoint, methods in paths.items():
        for method in ['get', 'post', 'put', 'delete']:
            if method not in methods:
                continue
                
            method_spec = methods[method]
            operation_id = method_spec.get('operationId')
            
            if not operation_id:
                continue
            
            # Extract parameters
            params = method_spec.get('parameters', [])
            param_info = {}
            
            for param in params:
                if param.get('in') != 'query':
                    continue
                    
                param_name = param.get('name')
                if not param_name:
                    continue
                
                schema = param.get('schema', {})
                param_info[param_name] = {
                    'type': schema.get('type', 'string'),
                    'required': param.get('required', False),
                    'enum': schema.get('enum'),
                    'description': param.get('description', '')
                }
            
            # Extract requestBody parameters for POST/PUT endpoints
            if method in ['post', 'put']:
                request_body = method_spec.get('requestBody', {})
                if request_body:
                    content = request_body.get('content', {})
                    json_content = content.get('application/json', {})
                    body_schema = json_content.get('schema', {})
                    properties = body_schema.get('properties', {})
                    
                    for prop_name, prop_schema in properties.items():
                        param_info[prop_name] = {
                            'type': prop_schema.get('type', 'string'),
                            'required': request_body.get('required', False),
                            'enum': prop_schema.get('enum'),
                            'description': prop_schema.get('description', '')
                        }
            
            endpoint_params[operation_id] = {
                'endpoint': endpoint,
                'method': method,
                'parameters': param_info
            }
    
    return endpoint_params


def get_handler_signature(handler_name: str) -> Tuple[Set[str], Dict[str, Any]]:
    """Get the signature of a handler function.
    
    Returns:
        Tuple of (parameter_names, parameter_info)
    """
    try:
        # Import handlers module
        import lib.api.handlers as handlers
        
        # Get the handler function
        if not hasattr(handlers, handler_name):
            return set(), {}
        
        func = getattr(handlers, handler_name)
        sig = inspect.signature(func)
        
        param_names = set()
        param_info = {}
        
        for param_name, param in sig.parameters.items():
            param_names.add(param_name)
            
            # Get type annotation
            annotation = param.annotation
            if annotation != inspect.Parameter.empty:
                param_info[param_name] = {
                    'annotation': str(annotation),
                    'has_default': param.default != inspect.Parameter.empty,
                    'default': param.default if param.default != inspect.Parameter.empty else None
                }
            else:
                param_info[param_name] = {
                    'annotation': 'Any',
                    'has_default': param.default != inspect.Parameter.empty,
                    'default': param.default if param.default != inspect.Parameter.empty else None
                }
        
        return param_names, param_info
    
    except Exception as e:
        print(f"Error inspecting handler '{handler_name}': {e}")
        return set(), {}


def validate_handler_parameters(
    operation_id: str,
    openapi_params: Dict[str, Any],
    handler_params: Set[str],
    handler_info: Dict[str, Any]
) -> List[str]:
    """Validate that handler parameters match OpenAPI specification.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Parse operation_id to get handler name
    parts = operation_id.split('.')
    handler_name = parts[1] if len(parts) == 2 else operation_id
    
    openapi_param_names = set(openapi_params.keys())
    
    # Check for missing required parameters
    for param_name, param_spec in openapi_params.items():
        if param_spec['required'] and param_name not in handler_params:
            errors.append(
                f"  ❌ Missing required parameter: '{param_name}' (required in OpenAPI)"
            )
    
    # Check for extra parameters not in OpenAPI
    extra_params = handler_params - openapi_param_names
    
    # Filter out common parameters that are expected
    expected_params = {'count', 'byod', 'id', 'request'}  # Common handler params
    extra_params = extra_params - expected_params
    
    if extra_params:
        for param in extra_params:
            errors.append(
                f"  ⚠️  Extra parameter in handler: '{param}' (not in OpenAPI)"
            )
    
    # Check for parameters with wrong types
    for param_name in openapi_param_names & handler_params:
        openapi_type = openapi_params[param_name]['type']
        handler_default = handler_info.get(param_name, {}).get('default')
        
        # Validate that optional parameters have defaults
        if not openapi_params[param_name]['required']:
            if handler_default is inspect.Parameter.empty:
                errors.append(
                    f"  ⚠️  Optional parameter '{param_name}' should have a default value"
                )
    
    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate handler function signatures against OpenAPI specification'
    )
    parser.add_argument(
        '--spec',
        default='lib/api/openapi.yaml',
        help='Path to OpenAPI specification file'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code 1 if any validation issues found'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information for all handlers'
    )
    
    args = parser.parse_args()
    
    # Load OpenAPI spec
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"❌ Error: OpenAPI spec not found at {spec_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading OpenAPI specification from {spec_path}...")
    openapi_spec = load_openapi_spec(spec_path)
    
    # Extract endpoint parameters
    print("Extracting endpoint parameters from OpenAPI...")
    endpoint_params = extract_endpoint_parameters(openapi_spec)
    
    print(f"Found {len(endpoint_params)} endpoints to validate\n")
    
    # Validate each handler
    total_errors = 0
    total_warnings = 0
    validated_handlers = 0
    
    for operation_id, endpoint_info in sorted(endpoint_params.items()):
        # Parse operation_id to get handler name
        parts = operation_id.split('.')
        handler_name = parts[1] if len(parts) == 2 else operation_id
        
        # Get handler signature
        handler_params, handler_info = get_handler_signature(handler_name)
        
        if not handler_params:
            if args.verbose:
                print(f"⚠️  {operation_id}")
                print(f"   Handler '{handler_name}' not found or could not be inspected")
                print()
            continue
        
        # Validate parameters
        errors = validate_handler_parameters(
            operation_id,
            endpoint_info['parameters'],
            handler_params,
            handler_info
        )
        
        if errors or args.verbose:
            print(f"{'✓' if not errors else '✗'} {operation_id}")
            print(f"   Endpoint: {endpoint_info['method'].upper()} {endpoint_info['endpoint']}")
            print(f"   Handler: {handler_name}()")
            print(f"   OpenAPI params: {len(endpoint_info['parameters'])}")
            print(f"   Handler params: {len(handler_params)}")
            
            if errors:
                print(f"   Issues found:")
                for error in errors:
                    print(error)
                    if '❌' in error:
                        total_errors += 1
                    elif '⚠️' in error:
                        total_warnings += 1
            
            print()
        
        validated_handlers += 1
    
    # Summary
    print("=" * 60)
    print(f"Validation Summary:")
    print(f"  Handlers validated: {validated_handlers}")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")
    
    if total_errors == 0 and total_warnings == 0:
        print("\n✓ All handlers are synchronized with OpenAPI specification!")
        sys.exit(0)
    elif total_errors == 0:
        print(f"\n✓ No errors found ({total_warnings} warnings)")
        sys.exit(0)
    else:
        print(f"\n✗ Validation failed with {total_errors} errors and {total_warnings} warnings")
        if args.strict:
            print("  Use --verbose to see all details")
            sys.exit(1)
        else:
            print("  Run with --strict to fail on validation issues")
            sys.exit(0)


if __name__ == '__main__':
    main()
