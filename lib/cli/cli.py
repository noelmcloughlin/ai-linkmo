"""The command-line door of AI-LinkMO.

The command tree is built from data, not written by hand. ``lib/api/api.yaml`` names the
classes the project exposes and the operations written by hand; the LinkML schema inside the
installed ``ai_atlas_nexus`` package gives each class its slots. ``lib.api.exposure`` joins
the two, and this module turns the result into one click command per exposed class, with one
option per slot, plus one command per hand path. Nothing here reads YAML or ``SchemaView``.

Every command runs in one of two modes. API mode, the default, sends the request to the
running server and prints what comes back. Local mode loads the ontology in this process and
calls the handler directly; it is slower by about ten seconds but needs no server.
"""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import click
import requests
from rich.console import Console
from rich.json import JSON as RichJSON

from lib.api.exposure import ExposedClass, Exposure, Parameter, load_exposure
from lib.cli.utils import (
    detect_server_url,
    display_error,
    display_result,
    invalidate_server_url_cache,
)

__all__ = ["build_cli", "main"]


try:
    __version__ = _pkg_version("acme-ai-atlas-nexus-demo")
except PackageNotFoundError:
    # The project is usually run from source with ``uv run`` rather than installed as a
    # distribution, so fall back to the version recorded in pyproject.toml.
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python below 3.11 is not supported
        tomllib = None  # type: ignore[assignment]

    __version__ = "0.0.0+unknown"
    if tomllib is not None:
        _pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        try:
            with _pyproject.open("rb") as _fp:
                __version__ = tomllib.load(_fp).get("project", {}).get("version", __version__)
        except OSError:
            pass

# Hosts that are always permitted for AI_ATLAS_API_URL without an explicit opt-in. Anything
# else requires AI_ATLAS_API_URL_ALLOW_REMOTE=1, so that an environment variable cannot
# silently point the CLI at an untrusted server that would then receive every query.
_LOCAL_API_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_DEFAULT_LOCAL_API_URL = "http://localhost:8000"


def _resolve_default_api_base_url() -> str:
    """Return a validated default API base URL.

    Accepts ``AI_ATLAS_API_URL`` only when the scheme is http or https and either the host is
    in the local allowlist or ``AI_ATLAS_API_URL_ALLOW_REMOTE`` is set to a truthy value.
    Otherwise it warns and falls back to ``http://localhost:8000``.
    """
    raw = os.getenv("AI_ATLAS_API_URL")
    if not raw:
        return _DEFAULT_LOCAL_API_URL

    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        sys.stderr.write(
            f"[warn] Ignoring invalid AI_ATLAS_API_URL={raw!r}; "
            f"falling back to {_DEFAULT_LOCAL_API_URL}.\n"
        )
        return _DEFAULT_LOCAL_API_URL

    allow_remote = os.getenv("AI_ATLAS_API_URL_ALLOW_REMOTE", "").lower() in (
        "1", "true", "yes", "on"
    )
    if parsed.hostname not in _LOCAL_API_HOSTS and not allow_remote:
        sys.stderr.write(
            f"[warn] AI_ATLAS_API_URL={raw!r} points to a non-local host. "
            f"Set AI_ATLAS_API_URL_ALLOW_REMOTE=1 to opt in. "
            f"Falling back to {_DEFAULT_LOCAL_API_URL}.\n"
        )
        return _DEFAULT_LOCAL_API_URL

    return raw


DEFAULT_API_BASE_URL = _resolve_default_api_base_url()
# Ports tried, in order, when the default URL does not answer.
COMMON_PORTS = [8000, 8080, 8888, 5000]
DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_MODE = "api"

# The options every command takes beside its filters. They control the CLI itself and never
# reach a handler or the server. They sit on the group too, so both ``./ai --count risk`` and
# ``./ai risk --count`` work; the command's value wins when both are given.
SHARED_OPTION_NAMES = ("mode", "timeout", "count", "verbose", "pretty")

HELP = """AI-LinkMO CLI Demo: query AI risk taxonomies, controls and related entities.

Each scope is one class of the AI Risk Ontology, or one of the operations written by hand.
Run ./ai <scope> -h to see the scope's filters, one per slot of the class. Give an id after
the scope to fetch one record.

API mode, the default, is fast and needs the server running. Local mode, --mode local, loads
the ontology in this process and works offline.
"""

EXAMPLES = """\b
Examples:
  ./ai taxonomy                                          list every taxonomy
  ./ai risk atlas-toxic-output                           one risk by id
  ./ai risk --isDefinedByTaxonomy nist-ai-rmf --count    count the risks of a taxonomy
  ./ai risk atlas-toxic-output --related                 the risks related to one risk
  ./ai taxonomy --byod                                   include the bring-your-own-data frameworks
  ./ai risk --count --mode local                         the same answer without a server
"""

console = Console()
logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False) -> None:
    """Set the logging level at run time, not at import time, so importing this module from
    a test leaves the global logging state alone. Only the library loggers known to be noisy
    are quietened."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, force=True)
    for logger_name in ("ai_atlas_nexus", "AIAtlasNexus", "linkml", "linkml_runtime"):
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(level)
        lib_logger.propagate = verbose


@dataclass(frozen=True)
class Target:
    """What a command stands for: the path it calls in API mode and the handler it calls in
    local mode. ``class_name`` is set for a class scope and None for a hand path."""

    scope: str
    path: str
    method: str
    operation_id: str
    class_name: str | None = None


@dataclass(frozen=True)
class Settings:
    """The resolved values of the shared options for one invocation."""

    mode: str = DEFAULT_MODE
    timeout: float = DEFAULT_REQUEST_TIMEOUT
    count: bool = False
    verbose: bool = False
    pretty: bool = False

    @property
    def show_pretty(self) -> bool:
        # Pretty printing is on when asked for, or when a person is reading a terminal. The
        # raw stdout descriptor is checked because sys.stdout may be wrapped by ``uv run``.
        is_tty = os.isatty(1) if hasattr(os, "isatty") else sys.stdout.isatty()
        return self.pretty or (not self.count and is_tty)


class _JsonValue(click.ParamType):
    """A request-body field given as a JSON string, for the arrays and objects of ``ares``."""

    name = "json"

    def convert(self, value, param, ctx):
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            self.fail(f"{value!r} is not valid JSON: {exc}", param, ctx)


def _shared_options() -> list[click.Option]:
    """A fresh set of the shared options. The mode and timeout default to None so that a
    value given on the group is not overridden by a command default."""
    return [
        click.Option(
            ["--mode", "mode"],
            type=click.Choice(["api", "local"]),
            default=None,
            metavar="MODE",
            help='Execution mode: "api" (fast, needs the server) or "local" (slow, offline). '
            f"Default {DEFAULT_MODE}.",
        ),
        click.Option(
            ["--timeout", "timeout"],
            type=float,
            default=None,
            metavar="SECONDS",
            help=f"HTTP request timeout in seconds. Default {DEFAULT_REQUEST_TIMEOUT}.",
        ),
        click.Option(["--count", "count"], is_flag=True, help="Print only the number of matches."),
        click.Option(
            ["--verbose", "verbose"],
            is_flag=True,
            help="Print the parsed arguments and the library's log messages.",
        ),
        click.Option(
            ["--pretty", "pretty"],
            is_flag=True,
            help="Indent and colour the JSON output. This is the default on a terminal.",
        ),
    ]


def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if value and not ctx.resilient_parsing:
        click.echo(f"{ctx.find_root().info_name} {__version__}")
        ctx.exit()


def _option(parameter: Parameter, required: bool = False) -> click.Option:
    """One click option for one parameter. The Python name is given explicitly so that click
    keeps the camelCase slot name, which is what the handlers and the server expect."""
    kwargs: dict[str, Any] = {
        "help": parameter.description or f"Filter by {parameter.name}",
        "required": required,
    }
    if parameter.kind == "boolean":
        kwargs["is_flag"] = True
    elif parameter.choices:
        kwargs["type"] = click.Choice(parameter.choices)
    elif parameter.kind in ("array", "object"):
        kwargs["type"] = _JsonValue()
    else:
        kwargs["type"] = {"integer": int, "number": float}.get(parameter.kind, str)
    return click.Option([f"--{parameter.name}", parameter.name], **kwargs)


def _id_argument() -> click.Argument:
    return click.Argument(["id"], required=False)


def _command(target: Target, help_text: str, params: list[click.Parameter]) -> click.Command:
    @click.pass_context
    def run(ctx: click.Context, **values: Any) -> None:
        _run(ctx, target, values)

    return click.Command(
        target.scope,
        params=params + _shared_options(),
        help=help_text,
        callback=run,
        context_settings={"help_option_names": ["-h", "--help"]},
    )


def _class_command(exposed: ExposedClass) -> click.Command:
    """The command for one exposed class: ``id`` is an optional positional argument and every
    other parameter of the class is an option."""
    params: list[click.Parameter] = []
    if exposed.parameter("id") is not None:
        params.append(_id_argument())
        note = (
            "Give an id to fetch one record, or omit it to list them all. "
            "Every other option filters the list; a record matches when the slot holds the value."
        )
    else:
        note = "This scope has no id argument. Every option filters the list."
    params += [_option(p) for p in exposed.parameters if p.name != "id"]
    help_text = f"{exposed.description}\n\n{note}" if exposed.description else note
    target = Target(
        scope=exposed.scope,
        path=exposed.path,
        method="get",
        operation_id=exposed.operation_id,
        class_name=exposed.name,
    )
    return _command(target, help_text, params)


def _overlay_parameter(definition: dict[str, Any]) -> Parameter:
    return Parameter(
        name=definition["name"],
        kind=definition.get("schema", {}).get("type", "string"),
        description=definition.get("description", "").strip(),
        slot=False,
    )


def _hand_command(path: str, methods: dict[str, Any]) -> click.Command | None:
    """The command for one hand path. The GET operation is used when there is one; ``ares``
    has only a POST and its options come from the request body's properties."""
    method = "get" if "get" in methods else next(iter(methods), None)
    if method is None:
        return None
    operation = methods[method]
    params: list[click.Parameter] = []
    for definition in operation.get("parameters", []):
        if definition.get("in") != "query":
            continue
        if definition["name"] == "id":
            params.append(_id_argument())
            continue
        params.append(_option(_overlay_parameter(definition), definition.get("required", False)))
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
    for name, schema in body.get("schema", {}).get("properties", {}).items():
        parameter = Parameter(
            name=name,
            kind=schema.get("type", "string"),
            description=schema.get("description", ""),
            slot=False,
        )
        params.append(_option(parameter))
    scope = path.strip("/")
    target = Target(
        scope=scope,
        path=path,
        method=method,
        operation_id=operation.get("operationId", f"handlers.{scope}"),
    )
    return _command(target, operation.get("summary", scope), params)


def _remember_shared(ctx: click.Context, **values: Any) -> None:
    """The group's callback keeps the shared options given before the scope."""
    ctx.obj = values


def build_cli(exposure: Exposure | None = None) -> click.Group:
    """Build the whole command tree from the exposure."""
    exposure = exposure or load_exposure()
    group = click.Group(
        name="ai",
        help=HELP,
        epilog=EXAMPLES,
        subcommand_metavar="<scope> [id] [--options]",
        params=_shared_options()
        + [
            click.Option(
                ["--version"],
                is_flag=True,
                is_eager=True,
                expose_value=False,
                callback=_print_version,
                help="Show the CLI version and exit.",
            )
        ],
        callback=click.pass_context(_remember_shared),
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    for exposed in exposure.classes.values():
        group.add_command(_class_command(exposed))
    for path, methods in exposure.hand_paths.items():
        command = _hand_command(path, methods)
        if command is not None:
            group.add_command(command)
    return group


def _settings(ctx: click.Context, values: dict[str, Any]) -> Settings:
    """Resolve the shared options, taking them out of ``values``. A flag given at either level
    is on; the mode and the timeout take the command's value, then the group's, then the
    default."""
    group_values = ctx.find_object(dict) or {}
    picked: dict[str, Any] = {}
    for name in SHARED_OPTION_NAMES:
        command_value = values.pop(name, None)
        group_value = group_values.get(name)
        if name in ("count", "verbose", "pretty"):
            picked[name] = bool(command_value) or bool(group_value)
        elif command_value is not None:
            picked[name] = command_value
        elif group_value is not None:
            picked[name] = group_value
    return Settings(**picked)


def _run(ctx: click.Context, target: Target, values: dict[str, Any]) -> None:
    """Carry out one command in the chosen mode."""
    settings = _settings(ctx, values)
    if settings.verbose:
        _configure_logging(verbose=True)
        console.print("\n[bold cyan][Parsed Arguments][/bold cyan]")
        for name, value in values.items():
            console.print(f"  {name}: {value}")
        console.print(f"[bold cyan][Operation ID: {target.operation_id}][/bold cyan]")
        console.print(f"[bold cyan][Mode: {settings.mode}][/bold cyan]")
    # An option the user did not give is None, or False for a flag, and neither is sent.
    request = {k: v for k, v in values.items() if v is not None and v is not False}
    if settings.mode == "api":
        call_api_server(target, request, settings)
    else:
        call_local_handler(target, request, settings)


def call_api_server(
    target: Target,
    request: dict[str, Any],
    settings: Settings,
    base_url: str = DEFAULT_API_BASE_URL,
) -> None:
    """Send the request to the server and print the answer. The server's port is detected when
    the default URL does not answer."""
    detected_url = detect_server_url(base_url, COMMON_PORTS)
    if detected_url:
        url = detected_url + target.path
        if settings.verbose and detected_url != base_url:
            console.print(f"[dim]Using server at {detected_url}[/dim]")
    else:
        url = base_url + target.path

    response = None
    try:
        if target.method == "post":
            response = requests.post(url, json=request, timeout=settings.timeout, verify=True)
        else:
            response = requests.get(url, params=request, timeout=settings.timeout, verify=True)
        response.raise_for_status()

        if settings.count:
            try:
                result = json.loads(response.text)
                if isinstance(result, dict) and "count" in result:
                    print(result["count"])
                else:
                    print(response.text)
            except json.JSONDecodeError:
                print(response.text)
        elif settings.show_pretty:
            try:
                json.loads(response.text)
                console.print(RichJSON(response.text))
            except json.JSONDecodeError:
                print(response.text)
        else:
            # Plain print, because Rich would wrap long lines and break the JSON for a pipe.
            print(response.text)

    except requests.exceptions.Timeout:
        display_error(
            "Timeout Error",
            f"Request to {url} timed out after {settings.timeout}s. "
            "Please check if the server is running.",
        )
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        # Make the next detection probe again instead of reusing the dead host until the
        # cache expires.
        invalidate_server_url_cache()
        parsed = urlparse(base_url)
        attempted_hosts = {base_url}
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        for port in COMMON_PORTS:
            attempted_hosts.add(f"{scheme}://{host}:{port}")
        attempted = ", ".join(sorted(attempted_hosts))
        display_error(
            "Connection Error",
            f"Could not connect to API server at {base_url}.\n"
            f"Tried: {attempted}\n\n"
            f"Is the server running? Start it with: "
            f"uv run uvicorn lib.api.server:app --reload",
        )
        sys.exit(1)
    except requests.exceptions.HTTPError:
        status = response.status_code if response is not None else "?"
        body = response.text if response is not None else ""
        display_error("HTTP Error", f"HTTP {status}: {body}")
        sys.exit(1)
    except Exception as e:
        display_error("Error", f"Unexpected error: {str(e)}")
        sys.exit(1)


def call_local_handler(target: Target, request: dict[str, Any], settings: Settings) -> None:
    """Call the handler in this process. A class scope goes through ``query_class``; a hand
    path goes to the function its ``operationId`` names, with the arguments its signature
    accepts."""
    from fastapi import HTTPException

    if not settings.verbose:
        # The library sets up its own logger, at INFO, when it is first loaded, which happens
        # inside the handler call. Disabling logging as a whole covers loggers created later.
        logging.disable(logging.CRITICAL)

    try:
        handlers = importlib.import_module("lib.api.handlers")
        if target.class_name is not None:
            func = handlers.query_class
            call_args = dict(request, class_name=target.class_name)
        else:
            func = getattr(handlers, target.operation_id.split(".")[-1])
            accepted = set(inspect.signature(func).parameters)
            call_args = {k: v for k, v in request.items() if k in accepted}
        try:
            result = func(**call_args)
        except HTTPException as e:
            display_error("API Error", f"[{e.status_code}] {e.detail}")
            sys.exit(1)
        display_result(result, count_only=settings.count, pretty=settings.show_pretty)
    except ModuleNotFoundError as e:
        display_error("Import Error", f"Handler module not found: {e}")
        sys.exit(1)
    except AttributeError:
        display_error(
            "Not Implemented", f"Handler for operationId '{target.operation_id}' not implemented"
        )
        sys.exit(1)
    except Exception as e:
        display_error("Error", f"Unexpected error: {str(e)}")
        logger.exception("Error in local handler")
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    """Entry point: ``uv run -m lib.cli.cli`` through the ``ai`` launcher."""
    _configure_logging(verbose=False)
    build_cli().main(args=argv, prog_name="./ai")


if __name__ == "__main__":
    main()
