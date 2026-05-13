"""
Dynamic FastAPI Server Generator

Generates FastAPI endpoints dynamically for all API operations.
Uses OpenAPI spec as single source of truth.

Usage:
    register_endpoints_from_openapi(app)
"""

from fastapi import FastAPI, Query, Body, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, Callable
import yaml
import inspect
from pathlib import Path
from lib.api import handlers


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


def create_get_endpoint(app: FastAPI, path: str, spec: Dict) -> None:
    """Dynamically create a GET endpoint from OpenAPI spec.
    
    Args:
        app: FastAPI application instance
        path: Endpoint path (e.g., '/risk')
        spec: OpenAPI operation specification
    """
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return
    
    handler_name = operation_id.replace('handlers.', '')
    
    # Check if handler exists
    if not hasattr(handlers, handler_name):
        print(f"⚠️  Warning: Handler '{handler_name}' not found, skipping {path}")
        return
    
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
        
        # Create parameter with Query() for FastAPI
        if required:
            default = Query(..., description=description)
        else:
            default = Query(default_value, description=description)
        
        param_annotations[name] = Optional[param_type]
        func_params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Optional[param_type],
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
            raise HTTPException(status_code=500, detail=str(e))
    
    # Set proper signature for FastAPI
    endpoint_func.__signature__ = inspect.Signature(parameters=func_params)
    endpoint_func.__name__ = f"get_{handler_name}"
    endpoint_func.__doc__ = spec.get('summary', f"Get {handler_name}")
    
    # Register with FastAPI
    app.get(path)(endpoint_func)
    print(f"✅ Registered GET {path} -> handlers.{handler_name}")


def create_post_endpoint(app: FastAPI, path: str, spec: Dict) -> None:
    """Dynamically create a POST endpoint from OpenAPI spec.
    
    Args:
        app: FastAPI application instance
        path: Endpoint path (e.g., '/ares')
        spec: OpenAPI operation specification
    """
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return
    
    handler_name = operation_id.replace('handlers.', '')
    
    if not hasattr(handlers, handler_name):
        print(f"⚠️  Warning: Handler '{handler_name}' not found, skipping POST {path}")
        return
    
    handler_func = getattr(handlers, handler_name)
    request_body = spec.get('requestBody', {})
    
    if request_body:
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
                raise HTTPException(status_code=500, detail=str(e))
        
        endpoint_func.__signature__ = inspect.Signature(parameters=func_params)
        endpoint_func.__name__ = f"post_{handler_name}"
        endpoint_func.__doc__ = spec.get('summary', f"Post {handler_name}")
        
        app.post(path)(endpoint_func)
        print(f"✅ Registered POST {path} -> handlers.{handler_name}")


def create_put_endpoint(app: FastAPI, path: str, spec: Dict) -> None:
    """Dynamically create a PUT endpoint from OpenAPI spec."""
    operation_id = spec.get('operationId', '')
    if not operation_id.startswith('handlers.'):
        return
    
    handler_name = operation_id.replace('handlers.', '')
    
    if not hasattr(handlers, handler_name):
        print(f"⚠️  Warning: Handler '{handler_name}' not found, skipping PUT {path}")
        return
    
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
    
    # Add request body parameter
    query_params.append(
        inspect.Parameter(
            'request',
            inspect.Parameter.KEYWORD_ONLY,
            annotation=Request,
            default=None
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
            raise HTTPException(status_code=500, detail=str(e))
    
    endpoint_func.__signature__ = inspect.Signature(parameters=query_params)
    endpoint_func.__name__ = f"put_{handler_name}"
    endpoint_func.__doc__ = spec.get('summary', f"Put {handler_name}")
    
    app.put(path)(endpoint_func)
    print(f"✅ Registered PUT {path} -> handlers.{handler_name}")


def register_endpoints_from_openapi(app: FastAPI, verbose: bool = True) -> int:
    """Register all endpoints dynamically from OpenAPI specification.
    
    This function reads the OpenAPI spec and generates FastAPI endpoints automatically.
    
    Args:
        app: FastAPI application instance
        verbose: Print registration messages
        
    Returns:
        Number of endpoints registered
    """
    spec = load_openapi_spec()
    paths = spec.get('paths', {})
    
    registered_count = 0
    
    for path, methods in paths.items():
        for method, method_spec in methods.items():
            method_lower = method.lower()
            
            if method_lower == 'get':
                create_get_endpoint(app, path, method_spec)
                registered_count += 1
            elif method_lower == 'post':
                create_post_endpoint(app, path, method_spec)
                registered_count += 1
            elif method_lower == 'put':
                create_put_endpoint(app, path, method_spec)
                registered_count += 1
            # and so on.
    
    if verbose:
        print(f"\n🎉 Registered {registered_count} endpoints from OpenAPI spec")
    
    return registered_count


# Usage
if __name__ == "__main__":
    app = FastAPI(
        title="AI-LinkMO API Demo",
        description="REST API for AI-LinkMO Demo operations (Dynamic Generation)"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root redirect
    @app.get("/", include_in_schema=False)
    def redirect_root():
        return RedirectResponse(url="/docs")
    
    # Health check
    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}
    
    # Dynamically register all endpoints from OpenAPI spec
    print("\n🚀 Generating endpoints from OpenAPI specification...")
    register_endpoints_from_openapi(app, verbose=True)
