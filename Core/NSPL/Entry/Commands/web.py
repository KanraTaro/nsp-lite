from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, List

from Core.NSPL.Entry.context import EntryContext
from Core.NSPL.Entry.Discovery.web_loader import discover_web_apps
from Core.NSPL.Entry.errors import (
    DuplicateWebAppError,
    InvalidWebApp,
    MissingWebDependencyError,
    WebAppNotFound,
    WebEntryError,
)
from Core.NSPL.Entry.web_context import WebContext


def _get_web_root(default_root: Path) -> Path:
    override = os.environ.get("WEB_ROOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            return (default_root / path).resolve()
        return path
    return (default_root / "Web").resolve()


def _build_top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Entry web",
        description="NSPL Web surface",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List available Web apps",
        description="Discover and list all Web apps without importing them",
    )
    list_parser.add_argument("--detailed", action="store_true")

    launch_parser = subparsers.add_parser(
        "launch",
        help="Launch a Web app in the foreground",
        description="Launch a local foreground Web app by canonical name",
    )
    launch_parser.add_argument("name", help="Canonical Web app name")
    launch_parser.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    launch_parser.add_argument("--port", type=int, default=None, help="Bind port")
    launch_parser.add_argument("--reload", action="store_true", help="Enable Uvicorn reload mode")
    launch_parser.add_argument("--log-level", default="info", help="Uvicorn log level")

    return parser


def _print_web_listing(registry: dict, detailed: bool = False) -> None:
    for name in sorted(registry.keys()):
        entry = registry[name]
        if detailed:
            meta = entry.get("meta", {})
            print(f"{name}\t{meta.get('version')}\t{meta.get('description')}")
        else:
            print(name)


def _descriptor_default_port(descriptor: dict) -> int:
    meta = descriptor.get("meta", {})
    if isinstance(meta, dict):
        raw_port = meta.get("default_port")
        try:
            if raw_port is not None:
                return int(raw_port)
        except (TypeError, ValueError):
            pass
    return 8765


def _descriptor_default_host(descriptor: dict) -> str:
    meta = descriptor.get("meta", {})
    if isinstance(meta, dict):
        raw_host = meta.get("default_host")
        if isinstance(raw_host, str) and raw_host.strip():
            return raw_host.strip()
    return "127.0.0.1"


def _load_uvicorn_runner() -> Callable[..., Any]:
    try:
        import uvicorn
    except ImportError as e:
        raise MissingWebDependencyError("uvicorn[standard]") from e
    return uvicorn.run


def _build_web_context(
    *,
    entry_context: EntryContext,
    web_root: Path,
    descriptor: dict,
) -> WebContext:
    meta = descriptor.get("meta", {})
    if not isinstance(meta, dict):
        raise InvalidWebApp(str(descriptor.get("entry_path", "")), "descriptor metadata is invalid")

    return WebContext(
        repo_root=entry_context.repo_root,
        caller_cwd=entry_context.caller_cwd,
        web_root=web_root,
        app_dir=Path(descriptor["web_dir"]).resolve(),
        metadata=dict(meta),
        entry_path=Path(descriptor["entry_path"]).resolve(),
        factory_name=str(descriptor.get("factory", "create_app")),
    )


def _load_app_from_descriptor(*, descriptor: dict, web_context: WebContext) -> Any:
    entry_path = Path(descriptor["entry_path"]).resolve()
    try:
        from Core.NSPL.Entry.Discovery.web_loader import load_web_module

        module = load_web_module(entry_path)
    except ImportError as e:
        missing_name = str(getattr(e, "name", None) or e).split()[0]
        raise MissingWebDependencyError(missing_name) from e

    factory = getattr(module, web_context.factory_name, None)
    if factory is None or not callable(factory):
        raise InvalidWebApp(str(entry_path), f"missing or non-callable factory '{web_context.factory_name}'")

    try:
        app = factory(web_context)
    except ImportError as e:
        missing_name = str(getattr(e, "name", None) or e).split()[0]
        raise MissingWebDependencyError(missing_name) from e
    except Exception as e:
        raise InvalidWebApp(str(entry_path), f"factory '{web_context.factory_name}' failed: {e}") from e

    if not callable(app):
        raise InvalidWebApp(str(entry_path), f"factory '{web_context.factory_name}' did not return an ASGI app")

    return app


def _launch_web_app(
    *,
    app_name: str,
    host: str | None,
    port: int | None,
    reload: bool,
    log_level: str,
    context: EntryContext,
    web_root: Path,
    uvicorn_runner: Callable[..., Any] | None = None,
) -> int:
    registry = discover_web_apps(web_root)
    if app_name not in registry:
        raise WebAppNotFound(app_name)
    descriptor = registry[app_name]
    web_context = _build_web_context(entry_context=context, web_root=web_root, descriptor=descriptor)
    app = _load_app_from_descriptor(descriptor=descriptor, web_context=web_context)

    bind_host = host or _descriptor_default_host(descriptor)
    bind_port = int(port) if port is not None else _descriptor_default_port(descriptor)

    runner = uvicorn_runner or _load_uvicorn_runner()

    print(f"NSPL web: launching {app_name} at http://{bind_host}:{bind_port}")
    print("NSPL web: foreground local server; press Ctrl+C to stop.")

    runner(app, host=bind_host, port=bind_port, reload=bool(reload), log_level=str(log_level))
    return 0


def main(argv: List[str], context: EntryContext | None = None) -> int:
    if context is None:
        from Core.NSPL.Entry.entry import _default_context

        context = _default_context()

    top_parser = _build_top_parser()

    if not argv:
        top_parser.print_help()
        return 0

    if argv[0] in {"-h", "--help"}:
        top_parser.print_help()
        return 0

    command = argv[0]
    web_root = _get_web_root(context.repo_root)

    try:
        if command == "list":
            list_parser = argparse.ArgumentParser(prog="Entry web list")
            list_parser.add_argument("--detailed", action="store_true")
            list_args = list_parser.parse_args(argv[1:])
            registry = discover_web_apps(web_root)
            _print_web_listing(registry, detailed=bool(getattr(list_args, "detailed", False)))
            return 0

        if command == "launch":
            launch_parser = argparse.ArgumentParser(prog="Entry web launch")
            launch_parser.add_argument("name")
            launch_parser.add_argument("--host", default=None)
            launch_parser.add_argument("--port", type=int, default=None)
            launch_parser.add_argument("--reload", action="store_true")
            launch_parser.add_argument("--log-level", default="info")
            launch_args = launch_parser.parse_args(argv[1:])
            return _launch_web_app(
                app_name=str(launch_args.name),
                host=getattr(launch_args, "host", None),
                port=getattr(launch_args, "port", None),
                reload=bool(getattr(launch_args, "reload", False)),
                log_level=str(getattr(launch_args, "log_level", "info")),
                context=context,
                web_root=web_root,
            )

        print(f"Unknown web command: {command}", file=sys.stderr)
        top_parser.print_usage()
        return 2
    except DuplicateWebAppError as e:
        print(str(e), file=sys.stderr)
        return 1
    except WebEntryError as e:
        print(str(e), file=sys.stderr)
        return 1
