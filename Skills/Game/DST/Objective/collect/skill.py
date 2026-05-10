"""Game.DST.Objective.collect skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from Core.Game.DST.commands import (
    build_collect_objective_command,
    clamp_positive_int,
    normalize_prefab,
)
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", dest="title", default="Objective", help="Objective title")
    parser.add_argument("--text", dest="text", default="", help="Objective text")
    parser.add_argument("--target-prefab", dest="target_prefab", required=True, help="Target prefab")
    parser.add_argument("--target-count", dest="target_count", type=int, default=1, help="Target count")
    parser.add_argument("--reward-prefab", dest="reward_prefab", default="cutgrass", help="Reward prefab")
    parser.add_argument("--reward-count", dest="reward_count", type=int, default=3, help="Reward count")
    parser.add_argument("--target-userid", dest="target_userid", default="", help="Target DST userid")
    add_transport_args(parser)


def _objective_text(text: str, target_count: int, target_prefab: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned != "":
        return cleaned

    count = clamp_positive_int(target_count)
    prefab = normalize_prefab(target_prefab)
    return f"Collect {count} {prefab} for camp supplies."


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        text = _objective_text(args.text, args.target_count, args.target_prefab)
        payload = build_collect_objective_command(
            args.title,
            text,
            args.target_prefab,
            args.target_count,
            args.reward_prefab,
            args.reward_count,
            args.target_userid,
        )
    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(getattr(args, "path", "") or "roh_dst_command.json").expanduser()),
        }
        if getattr(ctx, "json", False):
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)
        return 1

    return write_command_payload(args, ctx, payload)
