"""
Dynamic FastAPI Server Generator

Generates FastAPI endpoints dynamically for all API operations.
Uses OpenAPI spec as single source of truth.

Usage:
    register_endpoints_from_openapi(app)
"""

import inspect
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from lib.api import handlers

logger = logging.getLogger(__name__)


def _wrap_handler_error(exc: Exception, handler_name: str) -> HTTPException:
    """Convert an arbitrary handler exception into a sanitized HTTPException.

    The full traceback is logged server-side; clients only see a generic
    message to avoid leaking implementation details.
    """
    logger.exception("Unhandled exception in handler '%s'", handler_name)
    return HTTPException(status_code=500, detail="Internal server error.")


def load_openapi_spec() -> Dict[str, Any]:
    """Load and parse the OpenAPI specification."""
    spec_path = Path(__file__).parent / "openapi.yaml"
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)


def python_type_from_openapi(param_schema: Dict) -> type:
    """Map OpenAPI schema types to Python types."""
    schema_type = param_schema.get('type', 'string')
    
    type_map = {
        'integer': int,
        'boolean': bool,
        'string': str,
        'number': float,
        'array': list,
        'object': dict,
    }
    
    return type_map.get(schema_type, str)


def create_get_endpoint(app: FastAPI, path: str, spec: Dict) -> bool:
    """Dynamically create a GET endpoint from OpenAPI spec.

    Args:
        app: FastAPI application instance
        path: Endpoint path (e.g., '/risk')
        spec: OpenAPI operation specification

    Returns:
        True if an endpoint was registered, False otherwise.
    """
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return False

    handler_name = operation_id.replace('handlers.', '')

    # Check if handler exists
    if not hasattr(handlers, handler_name):
        logger.warning("Handler '%s' not found, skipping GET %s", handler_name, path)
        return False

    handler_func = getattr(handlers, handler_name)
    parameters = spec.get('parameters', [])
    
    # Build dynamic function parameters
    func_params = []
    param_annotations = {}
    
    for param in parameters:
        if param.get('in') != 'query':
            continue

        name = param['name']
        schema = param.get('schema', {})
        param_type = python_type_from_openapi(schema)
        required = param.get('required', False)
        description = param.get('description', '')
        default_value = schema.get('default')

        # Required params must NOT be wrapped in ``Optional`` - that flips the
        # generated docs to ``nullable: true`` and lies about the contract.
        if required:
            annotation = param_type
            default = Query(..., description=description)
        else:
            annotation = Optional[param_type]
            default = Query(default_value, description=description)

        param_annotations[name] = annotation
        func_params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=annotation,
                default=default
            )
        )
    
    # Create the endpoint function
    def endpoint_func(**kwargs):
        """Dynamically generated endpoint."""
        try:
            result = handler_func(**kwargs)
            # If handler returns a FileResponse, return it directly
            if isinstance(result, FileResponse):
                return result
            return JSONResponse(content=jsonable_encoder(result))
        except HTTPException:
            raise
        except Exception as e:
            raise _wrap_handler_error(e, handler_name)

    # Set proper signature for FastAPI
    endpoint_func.__signature__ = inspect.Signature(parameters=func_params)
    endpoint_func.__name__ = f"get_{handler_name}"
    endpoint_func.__doc__ = spec.get('summary', f"Get {handler_name}")

    # Register with FastAPI
    app.get(path)(endpoint_func)
    logger.info("Registered GET %s -> handlers.%s", path, handler_name)
    return True


def create_post_endpoint(app: FastAPI, path: str, spec: Dict) -> bool:
    """Dynamically create a POST endpoint from OpenAPI spec.

    Args:
        app: FastAPI application instance
        path: Endpoint path (e.g., '/ares')
        spec: OpenAPI operation specification

    Returns:
        True if an endpoint was registered, False otherwise.
    """
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return False

    handler_name = operation_id.replace('handlers.', '')

    if not hasattr(handlers, handler_name):
        logger.warning("Handler '%s' not found, skipping POST %s", handler_name, path)
        return False

    handler_func = getattr(handlers, handler_name)
    request_body = spec.get('requestBody', {})

    if not request_body:
        return False

    # Handle JSON request body
    content_schema = request_body.get('content', {}).get('application/json', {}).get('schema', {})
    properties = content_schema.get('properties', {})

    # Build function parameters from request body schema
    func_params = []
    for prop_name, prop_schema in properties.items():
        param_type = python_type_from_openapi(prop_schema)
        description = prop_schema.get('description', '')

        func_params.append(
            inspect.Parameter(
                prop_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=param_type,
                default=Body(..., description=description)
            )
        )

    # Create endpoint function
    def endpoint_func(**kwargs):
        """Dynamically generated POST endpoint."""
        try:
            result = handler_func(**kwargs)
            return JSONResponse(content=jsonable_encoder(result))
        except HTTPException:
            raise
        except Exception as e:
            raise _wrap_handler_error(e, handler_name)

    endpoint_func.__signature__ = inspect.Signature(parameters=func_params)
    endpoint_func.__name__ = f"post_{handler_name}"
    endpoint_func.__doc__ = spec.get('summary', f"Post {handler_name}")

    app.post(path)(endpoint_func)
    logger.info("Registered POST %s -> handlers.%s", path, handler_name)
    return True


def create_put_endpoint(app: FastAPI, path: str, spec: Dict) -> bool:
    """Dynamically create a PUT endpoint from OpenAPI spec.

    Returns:
        True if an endpoint was registered, False otherwise.
    """
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return False

    handler_name = operation_id.replace('handlers.', '')

    if not hasattr(handlers, handler_name):
        logger.warning("Handler '%s' not found, skipping PUT %s", handler_name, path)
        return False

    handler_func = getattr(handlers, handler_name)
    parameters = spec.get('parameters', [])
    
    # Build query parameters
    query_params = []
    for param in parameters:
        if param.get('in') == 'query':
            name = param['name']
            schema = param.get('schema', {})
            param_type = python_type_from_openapi(schema)
            description = param.get('description', '')
            
            query_params.append(
                inspect.Parameter(
                    name,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=Optional[param_type],
                    default=Query(None, description=description)
                )
            )
    
    # Add request body parameter. We must NOT supply a default value here
    # because FastAPI only auto-injects ``Request`` when the parameter is
    # positional or kw-only with no default. The previous ``default=None``
    # made FastAPI pass ``None`` instead of the live request object and any
    # handler that called ``await request.stream()`` would crash with
    # AttributeError.
    query_params.append(
        inspect.Parameter(
            'request',
            inspect.Parameter.KEYWORD_ONLY,
            annotation=Request,
        )
    )
    
    # Create async endpoint function for PUT
    async def endpoint_func(**kwargs):
        """Dynamically generated PUT endpoint."""
        try:
            if inspect.iscoroutinefunction(handler_func):
                result = await handler_func(**kwargs)
            else:
                result = handler_func(**kwargs)
            return JSONResponse(content=jsonable_encoder(result))
        except HTTPException:
            raise
        except Exception as e:
            raise _wrap_handler_error(e, handler_name)

    endpoint_func.__signature__ = inspect.Signature(parameters=query_params)
    endpoint_func.__name__ = f"put_{handler_name}"
    endpoint_func.__doc__ = spec.get('summary', f"Put {handler_name}")

    app.put(path)(endpoint_func)
    logger.info("Registered PUT %s -> handlers.%s", path, handler_name)
    return True


def register_endpoints_from_openapi(app: FastAPI, verbose: bool = True) -> int:
    """Register all endpoints dynamically from OpenAPI specification.

    This function reads the OpenAPI spec and generates FastAPI endpoints automatically.

    Args:
        app: FastAPI application instance
        verbose: Log a summary line after registration finishes.

    Returns:
        Number of endpoints actually registered (skipped handlers are not counted).
    """
    spec = load_openapi_spec()
    paths = spec.get('paths', {})

    registered_count = 0

    for path, methods in paths.items():
        for method, method_spec in methods.items():
            method_lower = method.lower()

            if method_lower == 'get':
                if create_get_endpoint(app, path, method_spec):
                    registered_count += 1
            elif method_lower == 'post':
                if create_post_endpoint(app, path, method_spec):
                    registered_count += 1
            elif method_lower == 'put':
                if create_put_endpoint(app, path, method_spec):
                    registered_count += 1

    if verbose:
        logger.info("Registered %d endpoints from OpenAPI spec", registered_count)

    return registered_count
