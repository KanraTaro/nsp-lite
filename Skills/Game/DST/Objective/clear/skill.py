"""Game.DST.Objective.clear skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from Core.Game.DST.commands import build_clear_objective_command
from Core.Game.DST.paths import resolve_command_path
from Core.NSPL.File.write import write_json


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--path",
        dest="path",
        default=None,
        help=argparse.SUPPRESS,
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    path = str(Path(getattr(args, "path", "") or "roh_dst_command.json").expanduser())

    try:
        explicit_path = getattr(args, "path", None)
        path = str(Path(explicit_path).expanduser()) if explicit_path else str(resolve_command_path())
        payload = build_clear_objective_command()
        written_path = write_json(path, payload)
        result = {
            "ok": True,
            "path": str(Path(written_path).expanduser()),
            "command": payload,
        }

        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0

    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(path).expanduser()),
        }

        if getattr(ctx, "json", False):
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)

        return 1
