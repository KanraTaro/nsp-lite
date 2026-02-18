from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from Core.NSPL.ProjectRoot import get_effective_root

from .errors import DuplicateGUIError, GUICLIError, GUINotFound, InvalidGUI
from .loader import discover_guis, resolve_gui


def _get_gui_root(default_root: Path) -> Path:
    override = os.environ.get("GUI_ROOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            return (default_root / path).resolve()
        return path
    return (default_root / "GUI").resolve()


def _build_top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="GUICLI",
        description="NSPL GUICLI launcher",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List available GUIs",
        description="Discover and list all GUIs without importing them",
    )
    list_parser.add_argument("--detailed", action="store_true")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a specific GUI by canonical name",
        description="Launch a GUI by canonical name",
    )
    run_parser.add_argument("name", help="Canonical name of the GUI to run")
    run_parser.add_argument(
        "argv",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the GUI. Use `--` to separate if needed.",
    )

    return parser


def _print_gui_listing(registry: dict, detailed: bool = False) -> None:
    for name in sorted(registry.keys()):
        entry = registry[name]
        if detailed:
            meta = entry.get("meta", {})
            print(f"{name}\t{meta.get('version')}\t{meta.get('description')}")
        else:
            print(name)


def _dispatch_gui(name: str, passthrough_argv: List[str], gui_root: Path) -> int:
    descriptor, module = resolve_gui(name, gui_root)
    meta = descriptor.get("meta", {})

    # Strip the leading "--" if the user used it
    if passthrough_argv and passthrough_argv[0] == "--":
        passthrough_argv = passthrough_argv[1:]

    project_root = get_effective_root()

    # Best-effort logging (same stance as SkillCLI)
    try:
        import Core.NSPL.NodeCTX as node_ctx  # local import so we keep module surface simple

        node_ctx.log_event(
            root=project_root,
            instance_id=node_ctx.get_default_instance_id(),
            node_tag=node_ctx.get_default_node_tag(),
            global_scope=False,
            domain="GUICLI",
            file_name="guicli.jsonl",
            kind="gui_started",
            rotation=node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
            extra={
                "gui": str(name),
                "entry": str(descriptor.get("entry_path")),
                "argv": list(passthrough_argv),
                "meta_version": str(meta.get("version", "")),
            },
        )
    except Exception:
        pass

    start_monotonic = time.monotonic()
    try:
        result = module.main(passthrough_argv)  # type: ignore[attr-defined]
        exit_code = int(result) if isinstance(result, int) else 0
    except SystemExit as e:
        exit_code = int(e.code) if isinstance(e.code, int) else 1
    except Exception as e:
        exit_code = 1
        try:
            import Core.NSPL.NodeCTX as node_ctx

            duration_ms = int((time.monotonic() - start_monotonic) * 1000.0)
            node_ctx.log_event(
                root=project_root,
                instance_id=node_ctx.get_default_instance_id(),
                node_tag=node_ctx.get_default_node_tag(),
                global_scope=False,
                domain="GUICLI",
                file_name="guicli.jsonl",
                kind="gui_failed",
                rotation=node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
                extra={
                    "gui": str(name),
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "duration_ms": int(duration_ms),
                },
            )
        except Exception:
            pass
        raise
    else:
        try:
            import Core.NSPL.NodeCTX as node_ctx

            duration_ms = int((time.monotonic() - start_monotonic) * 1000.0)
            node_ctx.log_event(
                root=project_root,
                instance_id=node_ctx.get_default_instance_id(),
                node_tag=node_ctx.get_default_node_tag(),
                global_scope=False,
                domain="GUICLI",
                file_name="guicli.jsonl",
                kind="gui_finished",
                rotation=node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
                extra={
                    "gui": str(name),
                    "exit_code": int(exit_code),
                    "duration_ms": int(duration_ms),
                },
            )
        except Exception:
            pass

    return exit_code


def main(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    top_parser = _build_top_parser()

    if not argv:
        top_parser.print_help()
        return

    if argv[0] in {"-h", "--help"}:
        top_parser.print_help()
        return

    command = argv[0]
    project_root = get_effective_root()
    gui_root = _get_gui_root(project_root)

    try:
        if command == "list":
            list_parser = argparse.ArgumentParser(prog="GUICLI list")
            list_parser.add_argument("--detailed", action="store_true")
            list_args = list_parser.parse_args(argv[1:])
            registry = discover_guis(gui_root)
            _print_gui_listing(registry, detailed=bool(getattr(list_args, "detailed", False)))
            return

        if command == "run":
            if len(argv) < 2:
                print("Error: missing GUI name", file=sys.stderr)
                top_parser.print_usage()
                sys.exit(1)

            gui_name = argv[1]
            passthrough = argv[2:]
            exit_code = _dispatch_gui(gui_name, passthrough, gui_root)
            sys.exit(exit_code)

        print(f"Unknown command: {command}", file=sys.stderr)
        top_parser.print_usage()
        sys.exit(1)

    except DuplicateGUIError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except GUINotFound as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except InvalidGUI as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except GUICLIError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

