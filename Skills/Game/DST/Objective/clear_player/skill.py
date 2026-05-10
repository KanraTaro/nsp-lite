"""Game.DST.Objective.clear_player skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import TARGET_MODES, build_clear_player_objective_command
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-userid", dest="target_userid", default="", help="Target DST userid")
    parser.add_argument("--target-mode", dest="target_mode", default="first", choices=TARGET_MODES, help="Player targeting mode")
    parser.add_argument("--announce", dest="announce", action="store_true", default=True, help="Announce the clear")
    parser.add_argument("--no-announce", dest="announce", action="store_false", help="Do not announce the clear")
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_clear_player_objective_command(args.target_userid, args.target_mode, args.announce)
    return write_command_payload(args, ctx, payload)
