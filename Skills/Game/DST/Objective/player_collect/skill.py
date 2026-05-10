"""Game.DST.Objective.player_collect skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import (
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
    TARGET_MODES,
    build_player_collect_objective_command,
    clamp_positive_int,
    normalize_prefab,
)
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-userid", dest="target_userid", default="", help="Target DST userid")
    parser.add_argument("--target-mode", dest="target_mode", default="first", choices=TARGET_MODES, help="Player targeting mode")
    parser.add_argument("--title", dest="title", default="Objective", help="Objective title")
    parser.add_argument("--text", dest="text", default="", help="Objective text")
    parser.add_argument("--target-prefab", dest="target_prefab", required=True, choices=SAFE_COLLECT_PREFABS, help="Target prefab")
    parser.add_argument("--target-count", dest="target_count", type=int, default=1, help="Target count")
    parser.add_argument("--reward-prefab", dest="reward_prefab", default="cutgrass", choices=SAFE_REWARD_PREFABS, help="Reward prefab")
    parser.add_argument("--reward-count", dest="reward_count", type=int, default=3, help="Reward count")
    parser.add_argument("--announce", dest="announce", action="store_true", default=True, help="Announce the objective")
    parser.add_argument("--no-announce", dest="announce", action="store_false", help="Do not announce the objective")
    add_transport_args(parser)


def _objective_text(text: str, target_count: int, target_prefab: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned != "":
        return cleaned

    count = clamp_positive_int(target_count)
    prefab = normalize_prefab(target_prefab)
    return f"Collect {count} {prefab} for camp supplies."


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_player_collect_objective_command(
        args.title,
        _objective_text(args.text, args.target_count, args.target_prefab),
        args.target_prefab,
        args.target_count,
        args.reward_prefab,
        args.reward_count,
        args.target_userid,
        args.target_mode,
        args.announce,
    )
    return write_command_payload(args, ctx, payload)
