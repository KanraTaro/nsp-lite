"""Game.DST.Objective.status skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import build_objective_status_command
from Skills.Game.DST._command_skill import add_hidden_path_arg, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--all", dest="all", action="store_true", default=True, help="Request all objective statuses")
    parser.add_argument("--active-only", dest="all", action="store_false", help="Request active objective status only")
    add_hidden_path_arg(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_objective_status_command(args.all)
    return write_command_payload(args, ctx, payload)
