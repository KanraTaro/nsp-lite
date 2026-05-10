"""Game.DST.Chaos.spawn_enemy skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import (
    SAFE_ENEMY_PREFABS,
    TARGET_MODES,
    build_spawn_enemy_command,
)
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prefab", dest="prefab", required=True, choices=SAFE_ENEMY_PREFABS, help="Enemy prefab")
    parser.add_argument("--count", dest="count", type=int, default=1, help="Enemy count")
    parser.add_argument("--target-mode", dest="target_mode", default="first", choices=TARGET_MODES, help="Player targeting mode")
    parser.add_argument("--radius", dest="radius", type=int, default=8, help="Spawn radius")
    parser.add_argument("--announce", dest="announce", default="", help="Optional in-game announcement")
    parser.add_argument("--force-boss", dest="force_boss", action="store_true", help="Required for deerclops boss spawning after chaos tier 3")
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_spawn_enemy_command(
        args.prefab,
        args.count,
        args.target_mode,
        args.radius,
        args.announce,
        args.force_boss,
    )
    return write_command_payload(args, ctx, payload)
