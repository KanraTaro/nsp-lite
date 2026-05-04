"""Game.DST.Chaos.set_tier skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import build_set_chaos_tier_command
from Skills.Game.DST._command_skill import add_hidden_path_arg, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--chaos-tier", dest="chaos_tier", type=int, required=True, help="Chaos tier 0-3")
    parser.add_argument("--announce", dest="announce", default="", help="Optional in-game announcement")
    add_hidden_path_arg(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_set_chaos_tier_command(args.chaos_tier, args.announce)
    return write_command_payload(args, ctx, payload)
