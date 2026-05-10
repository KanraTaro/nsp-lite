"""Game.DST.Chaos.clear_enemies skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import build_clear_spawned_enemies_command
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--announce", dest="announce", default="", help="Optional in-game announcement")
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_clear_spawned_enemies_command(args.announce)
    return write_command_payload(args, ctx, payload)
