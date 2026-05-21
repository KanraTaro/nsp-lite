from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from Core.NSPL.Entry.context import EntryContext


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nspl",
        description="NSPL unified entrypoint.",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="surface", required=True)

    skill = subparsers.add_parser("skill", help="Run the skill surface")
    skill.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to SkillCLI")

    gui = subparsers.add_parser("gui", help="Run the GUI surface")
    gui.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to GUICLI")

    web = subparsers.add_parser("web", help="Run the Web surface")
    web.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to Web Entry")

    return parser


def _default_context() -> EntryContext:
    from Core.NSPL.ProjectRoot import get_effective_root

    repo_root = get_effective_root()
    caller_cwd = Path(os.environ.get("NSPL_CALLER_CWD", os.getcwd())).expanduser().resolve()
    return EntryContext.from_paths(repo_root=repo_root, caller_cwd=caller_cwd)


def _normalize_forwarded_args(argv: List[str]) -> List[str]:
    return [arg for arg in argv if arg != "--"]


def main(argv: List[str] | None = None, context: EntryContext | None = None) -> int:
    if argv is None:
        import sys

        argv = sys.argv[1:]

    if context is None:
        context = _default_context()

    parser = _build_parser()
    args = parser.parse_args(argv)
    forwarded = _normalize_forwarded_args(list(getattr(args, "args", [])))

    if args.surface == "skill":
        from Core.NSPL.Entry.Commands.skill import main as skill_main

        return skill_main(forwarded, context=context)

    if args.surface == "gui":
        from Core.NSPL.Entry.Commands.gui import main as gui_main

        return gui_main(forwarded, context=context)

    if args.surface == "web":
        from Core.NSPL.Entry.Commands.web import main as web_main

        return web_main(forwarded, context=context)

    parser.print_usage()
    return 2
