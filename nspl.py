#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List


def _repo_root_from_this_file() -> Path:
    # nspl.py lives at repo root, so this is the most reliable truth.
    return Path(__file__).resolve().parent


class _Pushd:
    def __init__(self, path: Path) -> None:
        self._path = Path(path).resolve()
        self._old: str | None = None

    def __enter__(self) -> None:
        self._old = os.getcwd()
        os.chdir(str(self._path))

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._old is not None:
            os.chdir(self._old)


def _bootstrap_root_on_syspath(repo_root: Path) -> None:
    root_str: str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nspl",
        description="NSPL gateway entrypoint (skills, guis, and future subsystems).",
        add_help=True,
    )

    p.add_argument(
        "--root",
        default=None,
        help="Override repo root (default: directory containing nspl.py).",
    )

    # Important: this is caller context, NOT ProjectRoot discovery.
    p.add_argument(
        "--cwd",
        default=None,
        help="Caller working directory context (default: current shell cwd).",
    )

    sub = p.add_subparsers(dest="sub", required=True)

    skill = sub.add_parser("skill", help="Forward to SkillCLI")
    skill.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to SkillCLI")

    gui = sub.add_parser("gui", help="Forward to GUICLI")
    gui.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to GUICLI")

    return p


def _forward_to_module_main(module_main, argv: List[str]) -> int:
    result = module_main(argv)
    if isinstance(result, int):
        return int(result)
    return 0


def main(argv: List[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    repo_root: Path = Path(args.root).expanduser().resolve() if args.root else _repo_root_from_this_file()

    caller_cwd: Path
    if args.cwd:
        caller_cwd = Path(args.cwd).expanduser().resolve()
    else:
        caller_cwd = Path(os.getcwd()).resolve()

    if not (repo_root / "Core").is_dir():
        print(f"nspl: invalid --root (missing Core/): {repo_root}", file=sys.stderr)
        return 2

    if not caller_cwd.exists():
        print(f"nspl: invalid --cwd (path does not exist): {caller_cwd}", file=sys.stderr)
        return 2

    _bootstrap_root_on_syspath(repo_root)

    # Export caller context for future skills/guis that want "relative to where I ran it".
    os.environ["NSPL_CALLER_CWD"] = str(caller_cwd)

    # Critical: run CLIs from repo_root so ProjectRoot discovery works reliably.
    with _Pushd(repo_root):
        if args.sub == "skill":
            from Core.NSPL.SkillCLI.skillcli import main as skill_main
            forwarded = [a for a in args.args if a != "--"]
            return _forward_to_module_main(skill_main, forwarded)

        if args.sub == "gui":
            from Core.NSPL.GUICLI.guicli import main as gui_main
            forwarded = [a for a in args.args if a != "--"]
            return _forward_to_module_main(gui_main, forwarded)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

