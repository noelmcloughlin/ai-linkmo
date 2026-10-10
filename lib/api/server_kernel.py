"""Register the API's endpoints from the exposure file and the ontology schema.

The API has two kinds of endpoint. A class listing, such as ``GET /risk``, is one GET per
class that ``lib/api/api.yaml`` exposes. Its query parameters are the slots of that class
in the LinkML schema, so a slot added upstream becomes a filter here without a code change,
and every listing is answered by ``handlers.query_class``. A hand-written operation, such as
``GET /graph`` or ``PUT /byo``, is an OpenAPI operation object in the overlay of the same
file, bound to the ``lib.api.handlers`` function its ``operationId`` names.

``lib/api/server.py`` calls ``register_class_endpoints`` and ``register_hand_endpoints`` in
its lifespan. FastAPI's own ``/openapi.json`` is then the API's contract.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Literal, Optional, Union

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, create_model

from lib.api import handlers
from lib.api.exposure import ExposedClass, Parameter, load_exposure

logger = logging.getLogger(__name__)

# The parameters of a class listing that ``query_class`` takes by name; every other
# parameter is a filter on a slot of the class.
_CONTROL_PARAMETERS = ("byod", "id", "related", "related_ids")

_PYTHON_TYPES = {"string": str, "integer": int, "number": float, "boolean": bool}


def _wrap_handler_error(exc: Exception, handler_name: str) -> HTTPException:
    """Log the full traceback and give the client a generic 500.

    The client sees nothing of the implementation; the log has the detail.
    """
    logger.exception("Unhandled exception in handler '%s'", handler_name)
    return HTTPException(status_code=500, detail="Internal server error.")


def _is_registered(app: FastAPI, path: str, method: str) -> bool:
    """True when ``app`` already routes ``method`` on ``path``.

    The lifespan registers endpoints each time the app starts, and a test client can start
    the same app more than once in one process, so registration is made idempotent.
    """
    return any(
        getattr(route, "path", None) == path and method in (getattr(route, "methods", None) or ())
        for route in app.routes
    )


# Class listings.


def _query_parameter(parameter: Parameter) -> inspect.Parameter:
    """One keyword-only parameter of an endpoint signature, typed from the schema.

    A boolean is a flag that defaults to false. An enum slot with values becomes a
    ``Literal`` so that FastAPI answers a value outside the enum with a 422 and lists the
    values in ``/openapi.json``. Everything else is optional and absent by default.
    """
    if parameter.kind == "boolean":
        annotation: Any = bool
        default: Any = False
    elif parameter.choices:
        annotation = Optional[Literal[parameter.choices]]
        default = None
    else:
        annotation = Optional[_PYTHON_TYPES.get(parameter.kind, str)]
        default = None
    return inspect.Parameter(
        parameter.name,
        inspect.Parameter.KEYWORD_ONLY,
        annotation=annotation,
        default=Query(default, description=parameter.description),
    )


def envelope_model(exposed: ExposedClass) -> type[BaseModel]:
    """The response model of a class listing, built once per class for the contract.

    The body is the envelope the web UI reads: ``items``, ``count`` and ``validation_errors``
    for a listing, or ``item`` alone for a lookup by id. ``items`` holds ids rather than
    records when ``related_ids`` is set, hence the union. The model documents the shape in
    ``/openapi.json``; the endpoint returns ``query_class``'s dict unchanged, so a listing
    carries no ``item`` key and a lookup no ``items`` key.
    """
    model = handlers._get_model(exposed.name)
    return create_model(
        f"Envelope_{exposed.name}",
        __doc__=f"A listing of {exposed.name} records, or one record looked up by id.",
        items=(list[Union[model, str]], Field(default=[], description="The matching records, or their ids with related_ids")),
        count=(int, Field(default=0, description="The number of items")),
        validation_errors=(list[str], Field(default=[], description="Records the ontology model rejected")),
        item=(Optional[model], Field(default=None, description="The record named by id, or null")),
    )


def _class_endpoint(exposed: ExposedClass):
    """The endpoint function of one class listing, with its signature built from the slots."""

    def endpoint(**kwargs: Any):
        control = {name: kwargs.pop(name) for name in _CONTROL_PARAMETERS if name in kwargs}
        filters = {name: value for name, value in kwargs.items() if value is not None}
        try:
            result = handlers.query_class(exposed.name, **control, **filters)
        except HTTPException:
            raise
        except Exception as exc:
            raise _wrap_handler_error(exc, exposed.operation_id)
        return JSONResponse(content=jsonable_encoder(result))

    endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        [_query_parameter(p) for p in exposed.parameters]
    )
    endpoint.__name__ = exposed.operation_id.replace(".", "_")
    endpoint.__doc__ = exposed.description
    return endpoint


def register_class_endpoints(app: FastAPI) -> int:
    """Register one GET per exposed class and return how many were added."""
    registered = 0
    for exposed in load_exposure().classes.values():
        if _is_registered(app, exposed.path, "GET"):
            continue
        app.get(
            exposed.path,
            operation_id=exposed.operation_id,
            summary=f"List {exposed.name}",
            description=exposed.description,
            response_model=envelope_model(exposed),
        )(_class_endpoint(exposed))
        logger.info("Registered GET %s for %s", exposed.path, exposed.name)
        registered += 1
    return registered


# Hand-written operations.


def _bound_handler(operation: dict[str, Any], method: str, path: str):
    """The handler function an operation's ``operationId`` names, or None with a warning."""
    operation_id = operation.get("operationId", "")
    if not operation_id.startswith("handlers."):
        return None, ""
    name = operation_id[len("handlers.") :]
    if not hasattr(handlers, name):
        logger.warning("Handler '%s' not found, skipping %s %s", name, method, path)
        return None, name
    return getattr(handlers, name), name


def _hand_query_parameters(operation: dict[str, Any]) -> list[inspect.Parameter]:
    """The query parameters of an operation object as signature parameters.

    A required parameter is not wrapped in ``Optional``, which would mark it nullable in
    the contract and misdescribe it.
    """
    parameters = []
    for param in operation.get("parameters", []):
        if param.get("in") != "query":
            continue
        schema = param.get("schema", {})
        python_type = _PYTHON_TYPES.get(schema.get("type", "string"), str)
        description = param.get("description", "")
        if param.get("required", False):
            annotation: Any = python_type
            default = Query(..., description=description)
        else:
            annotation = Optional[python_type]
            default = Query(schema.get("default"), description=description)
        parameters.append(
            inspect.Parameter(
                param["name"], inspect.Parameter.KEYWORD_ONLY, annotation=annotation, default=default
            )
        )
    return parameters


def _route_options(operation: dict[str, Any]) -> dict[str, Any]:
    """The keyword arguments the operation contributes to FastAPI's route decorator."""
    options: dict[str, Any] = {
        "operation_id": operation.get("operationId"),
        "summary": operation.get("summary"),
        "description": operation.get("description"),
    }
    if "security" in operation:
        options["openapi_extra"] = {"security": operation["security"]}
    return options


def _register_get(app: FastAPI, path: str, operation: dict[str, Any]) -> bool:
    handler, name = _bound_handler(operation, "GET", path)
    if handler is None:
        return False

    def endpoint(**kwargs: Any):
        try:
            result = handler(**kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            raise _wrap_handler_error(exc, name)
        # A file handler, such as byo, returns its response ready to send.
        if isinstance(result, FileResponse):
            return result
        return JSONResponse(content=jsonable_encoder(result))

    endpoint.__signature__ = inspect.Signature(_hand_query_parameters(operation))  # type: ignore[attr-defined]
    endpoint.__name__ = f"get_{name}"
    app.get(path, **_route_options(operation))(endpoint)
    logger.info("Registered GET %s for handlers.%s", path, name)
    return True


def _register_post(app: FastAPI, path: str, operation: dict[str, Any]) -> bool:
    handler, name = _bound_handler(operation, "POST", path)
    if handler is None:
        return False
    # The body is a JSON object whose properties become the handler's keyword arguments.
    body_schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    if not body_schema:
        return False
    parameters = [
        inspect.Parameter(
            prop_name,
            inspect.Parameter.KEYWORD_ONLY,
            annotation=_PYTHON_TYPES.get(prop_schema.get("type", "string"), str)
            if prop_schema.get("type") not in ("array", "object")
            else (list if prop_schema.get("type") == "array" else dict),
            default=Body(..., description=prop_schema.get("description", "")),
        )
        for prop_name, prop_schema in body_schema.get("properties", {}).items()
    ]

    def endpoint(**kwargs: Any):
        try:
            result = handler(**kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            raise _wrap_handler_error(exc, name)
        return JSONResponse(content=jsonable_encoder(result))

    endpoint.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    endpoint.__name__ = f"post_{name}"
    app.post(path, **_route_options(operation))(endpoint)
    logger.info("Registered POST %s for handlers.%s", path, name)
    return True


def _register_put(app: FastAPI, path: str, operation: dict[str, Any]) -> bool:
    handler, name = _bound_handler(operation, "PUT", path)
    if handler is None:
        return False
    parameters = _hand_query_parameters(operation)
    # The handler streams the raw body itself, so it takes the request. The parameter must
    # have no default, or FastAPI would pass that default instead of the live request.
    parameters.append(
        inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)
    )

    async def endpoint(**kwargs: Any):
        try:
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            raise _wrap_handler_error(exc, name)
        return JSONResponse(content=jsonable_encoder(result))

    endpoint.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    endpoint.__name__ = f"put_{name}"
    app.put(path, **_route_options(operation))(endpoint)
    logger.info("Registered PUT %s for handlers.%s", path, name)
    return True


_REGISTRARS = {"get": _register_get, "post": _register_post, "put": _register_put}


def _publish_security_schemes(app: FastAPI, overlay: dict[str, Any]) -> None:
    """Add the overlay's security schemes to the generated contract.

    ``PUT /byo`` declares ``ApiKeyAuth`` so that the contract shows the intended shape,
    which SECURITY.md describes, even though the demo server does not enforce it.
    """
    schemes = overlay.get("components", {}).get("securitySchemes")
    if not schemes or getattr(app, "_overlay_security_published", False):
        return
    original = app.openapi

    def openapi() -> dict[str, Any]:
        schema = original()
        schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(schemes)
        return schema

    app.openapi = openapi  # type: ignore[method-assign]
    app._overlay_security_published = True  # type: ignore[attr-defined]


def register_hand_endpoints(app: FastAPI) -> int:
    """Register the hand-written operations of the overlay and return how many were added."""
    exposure = load_exposure()
    registered = 0
    for path, methods in exposure.hand_paths.items():
        for method, operation in methods.items():
            register = _REGISTRARS.get(method.lower())
            if register is None or _is_registered(app, path, method.upper()):
                continue
            if register(app, path, operation):
                registered += 1
    _publish_security_schemes(app, exposure.overlay)
    return registered
