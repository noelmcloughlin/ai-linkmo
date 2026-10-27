"""Register the API's endpoints from the exposure file and the schema.

The API has two kinds of endpoint. A class listing, such as ``GET /dog``, is one GET per
exposed class. Its query parameters are the slots of the class, so a slot added to the
schema becomes a filter without a code change, and every listing is answered by
``handlers.query_class``. A hand operation, such as ``GET /summary``, is an OpenAPI
operation object in the exposure file's overlay, bound to the function in ``hand.py``
that its ``operationId`` names.

FastAPI's own ``/openapi.json`` is then the API's contract, with one ``Envelope_<Class>``
component per listing that wraps the datamodel's own model of the class.
"""

from __future__ import annotations

import copy
import importlib
import inspect
import logging
from typing import Any, Literal, Optional, Union

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, create_model

from . import settings
from .datamodel import model
from .exposure import ExposedClass, Parameter, load_exposure
from .handlers import QueryError, jsonable, query_class

logger = logging.getLogger(__name__)

_PYTHON_TYPES = {"string": str, "integer": int, "number": float, "boolean": bool}


def _internal_error(exc: Exception, name: str) -> HTTPException:
    """Log the traceback and give the client a plain 500 that reveals nothing inside."""
    logger.exception("Unhandled exception in %s", name)
    return HTTPException(status_code=500, detail="Internal server error.")


def _is_registered(app: FastAPI, path: str, method: str) -> bool:
    """True when ``app`` already routes ``method`` on ``path``, so registering twice is safe."""
    return any(
        getattr(route, "path", None) == path and method in (getattr(route, "methods", None) or ())
        for route in app.routes
    )


def _annotation(parameter: Parameter) -> Any:
    """The type of a parameter. An enum with values becomes a ``Literal``, so that FastAPI
    answers a value outside it with a 422 and lists the values in the contract."""
    if parameter.choices:
        return Optional[Literal[parameter.choices]]
    if parameter.kind == "array":
        return Optional[list]
    if parameter.kind == "object":
        return Optional[dict]
    return Optional[_PYTHON_TYPES.get(parameter.kind, str)]


def _query_parameter(parameter: Parameter, required: bool = False) -> inspect.Parameter:
    """One keyword-only parameter of an endpoint signature. A slot whose name is not a
    Python identifier keeps its own name in the API through an alias."""
    alias = parameter.name if parameter.python_name != parameter.name else None
    default = Query(... if required else None, description=parameter.description, alias=alias)
    annotation = _annotation(parameter)
    if required:
        annotation = annotation.__args__[0]
    return inspect.Parameter(
        parameter.python_name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation, default=default
    )


def envelope_model(exposed: ExposedClass) -> type[BaseModel]:
    """The response model of a class listing, for the contract.

    The body is the envelope a web UI reads: ``items``, ``count`` and ``validation_errors``
    for a listing, or ``item`` alone for a lookup by identifier. ``items`` may hold ids
    rather than records when a Python source returns them, hence the union.
    """
    record = model(exposed.name)
    return create_model(
        f"Envelope_{exposed.name}",
        __doc__=f"A listing of {exposed.name} records, or one record looked up by identifier.",
        items=(list[Union[record, str]], Field(default=[], description="The matching records")),
        count=(int, Field(default=0, description="The number of items")),
        validation_errors=(
            list[str],
            Field(default=[], description="Records in the data that the datamodel rejected"),
        ),
        item=(Optional[record], Field(default=None, description="The record named, or null")),
    )


def _class_endpoint(exposed: ExposedClass):
    names = {p.python_name: p.name for p in exposed.parameters}

    def endpoint(**kwargs: Any):
        params = {names[k]: v for k, v in kwargs.items() if v is not None}
        try:
            result = query_class(exposed.name, **params)
        except QueryError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail) from exc
        except Exception as exc:
            raise _internal_error(exc, exposed.operation_id) from exc
        return JSONResponse(content=result)

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
            summary=f"List {exposed.label}",
            description=exposed.description,
            response_model=envelope_model(exposed),
            tags=["classes"],
        )(_class_endpoint(exposed))
        registered += 1
    return registered


# Hand operations.


def _bound_handler(operation: dict[str, Any], method: str, path: str):
    """The function the operation's ``operationId`` names, as ``hand.<function>``."""
    operation_id = operation.get("operationId", "")
    module_name, _, function_name = operation_id.rpartition(".")
    if module_name != "hand" or not function_name:
        logger.warning("%s %s needs an operationId of the form hand.<function>", method, path)
        return None, operation_id
    settings.add_module_paths()
    module = importlib.import_module(".hand", __package__)
    function = getattr(module, function_name, None)
    if function is None:
        logger.warning("hand.%s is not defined; skipping %s %s", function_name, method, path)
    return function, function_name


def _hand_query_parameters(operation: dict[str, Any]) -> tuple[list[inspect.Parameter], dict[str, str]]:
    parameters, names = [], {}
    for definition in operation.get("parameters") or ():
        if definition.get("in") != "query":
            continue
        schema = definition.get("schema") or {}
        parameter = Parameter(
            name=definition["name"],
            kind=schema.get("type", "string"),
            description=" ".join((definition.get("description") or "").split()),
            choices=tuple(schema.get("enum") or ()),
            slot=False,
        )
        names[parameter.python_name] = parameter.name
        parameters.append(_query_parameter(parameter, required=definition.get("required", False)))
    return parameters, names


def _route_options(operation: dict[str, Any]) -> dict[str, Any]:
    options: dict[str, Any] = {
        "operation_id": operation.get("operationId"),
        "summary": operation.get("summary"),
        "description": operation.get("description"),
        "tags": operation.get("tags") or ["hand"],
    }
    if "security" in operation:
        options["openapi_extra"] = {"security": operation["security"]}
    return options


async def _call(function, kwargs: dict[str, Any]) -> Any:
    result = function(**kwargs)
    if inspect.isawaitable(result):
        result = await result
    return result


def _respond(result: Any) -> Response:
    if isinstance(result, Response):
        return result
    return JSONResponse(content=jsonable_encoder(jsonable(result)))


def _hand_endpoint(function, name: str, names: dict[str, str], parameters: list[inspect.Parameter]):
    accepted = set(inspect.signature(function).parameters)

    async def endpoint(**kwargs: Any):
        arguments = {names.get(k, k): v for k, v in kwargs.items()}
        arguments = {k: v for k, v in arguments.items() if k in accepted and v is not None}
        try:
            return _respond(await _call(function, arguments))
        except QueryError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise _internal_error(exc, name) from exc

    endpoint.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    endpoint.__name__ = f"hand_{name}"
    return endpoint


def _register_hand(app: FastAPI, path: str, method: str, operation: dict[str, Any]) -> bool:
    function, name = _bound_handler(operation, method.upper(), path)
    if function is None:
        return False
    parameters, names = _hand_query_parameters(operation)
    body = ((operation.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
    for prop_name, prop_schema in ((body.get("schema") or {}).get("properties") or {}).items():
        parameter = Parameter(name=prop_name, kind=prop_schema.get("type", "string"), slot=False)
        names[parameter.python_name] = prop_name
        parameters.append(
            inspect.Parameter(
                parameter.python_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=_annotation(parameter),
                default=Body(None, description=prop_schema.get("description", "")),
            )
        )
    if "request" in inspect.signature(function).parameters:
        # A handler that reads the raw request, such as an upload, gets it as ``request``.
        parameters.append(inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request))
    route = getattr(app, method.lower())
    route(path, **_route_options(operation))(_hand_endpoint(function, name, names, parameters))
    return True


def register_hand_endpoints(app: FastAPI) -> int:
    """Register the overlay's hand operations and return how many were added."""
    registered = 0
    for path, methods in load_exposure().hand_paths.items():
        for method, operation in (methods or {}).items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            if _is_registered(app, path, method.upper()):
                continue
            if _register_hand(app, path, method, operation or {}):
                registered += 1
    return registered


def _deep_merge(into: dict[str, Any], other: dict[str, Any]) -> None:
    for key, value in other.items():
        if isinstance(value, dict) and isinstance(into.get(key), dict):
            _deep_merge(into[key], value)
        else:
            into[key] = copy.deepcopy(value)


def publish_overlay(app: FastAPI) -> None:
    """Merge the overlay, all but its paths, into the generated contract.

    The paths are already routes. The rest, such as security schemes and shared
    responses, is added to what FastAPI builds, so the contract carries it too.
    """
    overlay = {k: v for k, v in load_exposure().overlay.items() if k != "paths"}
    if not overlay or getattr(app, "_overlay_published", False):
        return
    original = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = original()
            _deep_merge(schema, overlay)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
    app._overlay_published = True  # type: ignore[attr-defined]
