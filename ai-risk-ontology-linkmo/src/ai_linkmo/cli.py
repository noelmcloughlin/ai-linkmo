"""The command line, built from the schema and the exposure file.

The command tree is data, not code. ``exposure.py`` joins the exposure file and the schema,
and this module turns the result into one click command per exposed class, with one
option per slot of the class, plus one command per operation written by hand in the
exposure file's overlay. Nothing here reads YAML or SchemaView.

Every command runs in one of two modes. Local mode, the default, reads the data in this
process. API mode sends the same question to a running server and prints its answer.
The default mode comes from ``<PREFIX>_MODE`` and the server from ``<PREFIX>_API_URL``,
where the prefix is ``settings.ENV_PREFIX``.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as distribution_version
from typing import Any
from urllib import error as urlerror, parse, request as urlrequest

import click

from . import settings
from .exposure import ExposedClass, Exposure, Parameter, load_exposure
from .output import display_error, display_result

__all__ = ["SHARED_OPTION_NAMES", "build_cli", "main"]

DEFAULT_MODE = os.environ.get(f"{settings.ENV_PREFIX}_MODE", "local")
DEFAULT_TIMEOUT = 30.0

# The options every command takes beside its filters. They control the command line itself
# and never reach a handler or the server. They sit on the group as well, so both
# `cmd --count dog` and `cmd dog --count` work. The command's own value wins.
SHARED_OPTION_NAMES = ("mode", "timeout", "count", "pretty")

# Hosts the API URL may name without an explicit opt-in. Any other host needs
# <PREFIX>_API_URL_ALLOW_REMOTE=1, so that an environment variable cannot quietly send
# every question to a server nobody chose.
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_DEFAULT_API_URL = "http://localhost:8000"


def api_base_url() -> str:
    raw = os.environ.get(f"{settings.ENV_PREFIX}_API_URL", "")
    if not raw:
        return _DEFAULT_API_URL
    parsed = parse.urlparse(raw)
    allow_remote = os.environ.get(f"{settings.ENV_PREFIX}_API_URL_ALLOW_REMOTE", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        display_error("Warning", f"ignoring the API URL {raw!r}; using {_DEFAULT_API_URL}")
        return _DEFAULT_API_URL
    if parsed.hostname not in _LOCAL_HOSTS and not allow_remote:
        display_error(
            "Warning",
            f"the API URL {raw!r} is not local; set {settings.ENV_PREFIX}_API_URL_ALLOW_REMOTE=1 "
            f"to use it. Using {_DEFAULT_API_URL}",
        )
        return _DEFAULT_API_URL
    return raw.rstrip("/")


def project_version() -> str:
    try:
        return distribution_version(settings.DISTRIBUTION)
    except PackageNotFoundError:
        import tomllib

        try:
            with open(settings.PROJECT_DIR / "pyproject.toml", "rb") as handle:
                return tomllib.load(handle)["project"]["version"]
        except (OSError, KeyError):
            return "0.0.0+unknown"


@dataclass(frozen=True)
class Target:
    """What a command stands for: the path it calls in API mode and the handler it calls in
    local mode. ``class_name`` is set for a class listing and None for a hand operation."""

    scope: str
    path: str
    method: str
    operation_id: str
    names: dict[str, str]  # Python name of each parameter to its name in the API
    class_name: str | None = None


@dataclass(frozen=True)
class RunSettings:
    mode: str = DEFAULT_MODE
    timeout: float = DEFAULT_TIMEOUT
    count: bool = False
    pretty: bool = False


class _JsonValue(click.ParamType):
    """A value given as JSON text, for the arrays and objects of a hand operation's body."""

    name = "json"

    def convert(self, value, param, ctx):
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            self.fail(f"{value!r} is not valid JSON: {exc}", param, ctx)


def _shared_options() -> list[click.Option]:
    """A fresh set of the shared options. The mode and the timeout default to None so that
    a value given on the group is not overridden by a command's default."""
    return [
        click.Option(
            ["--mode", "mode"],
            type=click.Choice(["local", "api"]),
            default=None,
            help=f'"local" reads the data here, "api" asks the server. Default {DEFAULT_MODE}.',
        ),
        click.Option(
            ["--timeout", "timeout"],
            type=float,
            default=None,
            metavar="SECONDS",
            help=f"Seconds to wait for the server in API mode. Default {DEFAULT_TIMEOUT:g}.",
        ),
        click.Option(["--count", "count"], is_flag=True, help="Print only the number of records."),
        click.Option(["--pretty", "pretty"], is_flag=True, help="Indent the JSON, as on a terminal."),
    ]


def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if value and not ctx.resilient_parsing:
        click.echo(f"{ctx.find_root().info_name} {project_version()}")
        ctx.exit()


def _option(parameter: Parameter, required: bool = False) -> click.Option:
    """One click option for one parameter, under the parameter's own name, so that the
    command line spells a slot exactly as the schema and the API do."""
    kwargs: dict[str, Any] = {
        "help": parameter.description or f"Filter by {parameter.name}.",
        "required": required,
    }
    declarations = [f"--{parameter.name}", parameter.python_name]
    if parameter.kind == "boolean":
        # A flag with a negative form, so that leaving it out filters nothing.
        declarations = [f"--{parameter.name}/--no-{parameter.name}", parameter.python_name]
        kwargs["default"] = None
    elif parameter.choices:
        kwargs["type"] = click.Choice(parameter.choices)
    elif parameter.kind in ("array", "object"):
        kwargs["type"] = _JsonValue()
    else:
        kwargs["type"] = {"integer": int, "number": float}.get(parameter.kind, str)
    return click.Option(declarations, **kwargs)


def _command(target: Target, help_text: str, params: list[click.Parameter]) -> click.Command:
    @click.pass_context
    def run(ctx: click.Context, **values: Any) -> None:
        _run(ctx, target, values)

    return click.Command(
        target.scope,
        params=params + _shared_options(),
        help=help_text,
        short_help=help_text.split("\n", 1)[0][:80] or target.scope,
        callback=run,
        context_settings={"help_option_names": ["-h", "--help"]},
    )


def _class_command(exposed: ExposedClass) -> click.Command:
    """The command for one exposed class: its identifier is an optional argument and every
    other parameter is an option."""
    params: list[click.Parameter] = []
    names = {p.python_name: p.name for p in exposed.parameters}
    identifier = exposed.parameter(exposed.identifier) if exposed.identifier else None
    if identifier is not None:
        params.append(click.Argument([identifier.python_name], required=False))
        note = (
            f"Give the record's {identifier.name} to fetch it, or leave it out to list them all. "
            "Every option filters the list; a record matches when its slot holds the value."
        )
    else:
        note = "Every option filters the list; a record matches when its slot holds the value."
    params += [_option(p) for p in exposed.parameters if p is not identifier]
    help_text = f"{exposed.description}\n\n{note}" if exposed.description else note
    target = Target(
        scope=exposed.scope,
        path=exposed.path,
        method="get",
        operation_id=exposed.operation_id,
        names=names,
        class_name=exposed.name,
    )
    return _command(target, help_text, params)


def _overlay_parameter(definition: dict[str, Any]) -> Parameter:
    schema = definition.get("schema") or {}
    return Parameter(
        name=definition["name"],
        kind=schema.get("type", "string"),
        description=" ".join((definition.get("description") or "").split()),
        choices=tuple(schema.get("enum") or ()),
        slot=False,
    )


def _hand_command(path: str, methods: dict[str, Any]) -> click.Command | None:
    """The command for one hand operation: the GET when there is one, else the first
    method. Its options are the operation's query parameters and its body's properties.
    The first query parameter marked ``x-linkmo-argument: true`` is its argument instead,
    as the identifier is a class command's."""
    method = "get" if "get" in methods else next(iter(methods), None)
    if method is None:
        return None
    operation = methods[method]
    params: list[click.Parameter] = []
    names: dict[str, str] = {}
    for definition in operation.get("parameters") or ():
        if definition.get("in") != "query":
            continue
        parameter = _overlay_parameter(definition)
        names[parameter.python_name] = parameter.name
        required = definition.get("required", False)
        if definition.get("x-linkmo-argument") and not any(isinstance(p, click.Argument) for p in params):
            kind = {"integer": int, "number": float}.get(parameter.kind, str)
            params.insert(0, click.Argument([parameter.python_name], type=kind, required=required))
        else:
            params.append(_option(parameter, required))
    body = ((operation.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
    for name, schema in ((body.get("schema") or {}).get("properties") or {}).items():
        parameter = Parameter(
            name=name,
            kind=schema.get("type", "string"),
            description=schema.get("description", ""),
            slot=False,
        )
        names[parameter.python_name] = parameter.name
        params.append(_option(parameter))
    scope = path.strip("/")
    target = Target(
        scope=scope,
        path=path,
        method=method,
        operation_id=operation.get("operationId", f"hand.{scope}"),
        names=names,
    )
    return _command(target, operation.get("summary") or scope, params)


def _remember_shared(ctx: click.Context, **values: Any) -> None:
    """The group keeps the shared options given before the command."""
    ctx.obj = values


def _examples(exposure: Exposure) -> str:
    name = settings.COMMAND_NAME
    lines = ["\b", "Examples:"]
    for exposed in list(exposure.classes.values())[:1]:
        lines.append(f"  {name} {exposed.scope}")
        if exposed.identifier:
            lines.append(f"  {name} {exposed.scope} <{exposed.identifier}>")
        choice = next((p for p in exposed.parameters if p.choices), None)
        if choice is not None:
            lines.append(f"  {name} {exposed.scope} --{choice.name} {choice.choices[0]} --count")
        lines.append(f"  {name} {exposed.scope} --mode api")
    return "\n".join(lines)


def build_cli(exposure: Exposure | None = None) -> click.Group:
    """Build the whole command tree from the exposure."""
    exposure = exposure or load_exposure()
    group = click.Group(
        name=settings.COMMAND_NAME,
        help=(
            "Query the records of the schema's classes, one command per class.\n\n"
            f"Run {settings.COMMAND_NAME} <command> -h to see a command's filters, one per "
            "slot of its class."
        ),
        epilog=_examples(exposure),
        subcommand_metavar="<command> [id] [--options]",
        params=_shared_options()
        + [
            click.Option(
                ["--version"],
                is_flag=True,
                is_eager=True,
                expose_value=False,
                callback=_print_version,
                help="Print the version and exit.",
            )
        ],
        callback=click.pass_context(_remember_shared),
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    for exposed in exposure.classes.values():
        group.add_command(_class_command(exposed))
    for path, methods in exposure.hand_paths.items():
        command = _hand_command(path, methods or {})
        if command is not None:
            group.add_command(command)
    return group


def _settings(ctx: click.Context, values: dict[str, Any]) -> RunSettings:
    """Resolve the shared options and take them out of ``values``. A flag given at either
    level is on; the mode and the timeout take the command's value, then the group's."""
    group_values = ctx.find_object(dict) or {}
    picked: dict[str, Any] = {}
    for name in SHARED_OPTION_NAMES:
        command_value = values.pop(name, None)
        group_value = group_values.get(name)
        if name in ("count", "pretty"):
            picked[name] = bool(command_value) or bool(group_value)
        elif command_value is not None:
            picked[name] = command_value
        elif group_value is not None:
            picked[name] = group_value
    return RunSettings(**picked)


def _run(ctx: click.Context, target: Target, values: dict[str, Any]) -> None:
    run_settings = _settings(ctx, values)
    # A parameter the user did not give is None and is not sent.
    request = {target.names.get(k, k): v for k, v in values.items() if v is not None}
    if run_settings.mode == "api":
        call_api_server(target, request, run_settings)
    else:
        call_local_handler(target, request, run_settings)


def _query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def call_api_server(target: Target, request: dict[str, Any], run_settings: RunSettings) -> None:
    """Send the question to the server and print its answer."""
    url = api_base_url() + target.path
    data = None
    headers = {"Accept": "application/json"}
    if target.method == "get":
        query = parse.urlencode({k: _query_value(v) for k, v in request.items()}, doseq=True)
        if query:
            url = f"{url}?{query}"
    else:
        data = json.dumps(request).encode("utf-8")
        headers["Content-Type"] = "application/json"
    call = urlrequest.Request(url, data=data, headers=headers, method=target.method.upper())
    try:
        with urlrequest.urlopen(call, timeout=run_settings.timeout) as response:
            body = response.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        display_error("HTTP error", f"{exc.code} from {url}: {exc.read().decode('utf-8', 'replace')}")
        sys.exit(1)
    except (urlerror.URLError, TimeoutError) as exc:
        display_error(
            "Connection error",
            f"no answer from {url} ({getattr(exc, 'reason', exc)}). Is the server running? "
            "Start it with `just serve`, or use --mode local.",
        )
        sys.exit(1)
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return
    display_result(result, count_only=run_settings.count, pretty=run_settings.pretty)


def call_local_handler(target: Target, request: dict[str, Any], run_settings: RunSettings) -> None:
    """Answer in this process: a class listing through ``query_class``, a hand operation
    through the function its operationId names, with the arguments it accepts."""
    from fastapi import HTTPException

    from .handlers import QueryError, jsonable, query_class

    try:
        if target.class_name is not None:
            result = query_class(target.class_name, **request)
        else:
            settings.add_module_paths()
            module_name, _, function_name = target.operation_id.rpartition(".")
            module = importlib.import_module(f".{module_name or 'hand'}", __package__)
            function = getattr(module, function_name)
            accepted = set(inspect.signature(function).parameters)
            result = jsonable(function(**{k: v for k, v in request.items() if k in accepted}))
    except QueryError as exc:
        display_error("Error", f"[{exc.status}] {exc.detail}")
        sys.exit(1)
    except HTTPException as exc:
        # A hand operation may raise FastAPI's own exception, which the API answers as is.
        display_error("Error", f"[{exc.status_code}] {exc.detail}")
        sys.exit(1)
    except (FileNotFoundError, LookupError, ValueError, ImportError, AttributeError) as exc:
        display_error("Error", str(exc))
        sys.exit(1)
    display_result(result, count_only=run_settings.count, pretty=run_settings.pretty)


def main(argv: list[str] | None = None) -> None:
    build_cli().main(args=argv, prog_name=settings.COMMAND_NAME)


if __name__ == "__main__":
    main()
