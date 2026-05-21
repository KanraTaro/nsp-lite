from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

from Core.NSPL.Entry.context import EntryContext
from Core.NSPL.Entry.Discovery.web_loader import discover_web_apps
from Core.NSPL.Entry.errors import DuplicateWebAppError, WebEntryError


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

    return parser


def _print_web_listing(registry: dict, detailed: bool = False) -> None:
    for name in sorted(registry.keys()):
        entry = registry[name]
        if detailed:
            meta = entry.get("meta", {})
            print(f"{name}\t{meta.get('version')}\t{meta.get('description')}")
        else:
            print(name)


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

        print(f"Unknown web command: {command}", file=sys.stderr)
        top_parser.print_usage()
        return 2
    except DuplicateWebAppError as e:
        print(str(e), file=sys.stderr)
        return 1
    except WebEntryError as e:
        print(str(e), file=sys.stderr)
        return 1
