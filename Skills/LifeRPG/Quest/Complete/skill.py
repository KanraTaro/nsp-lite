from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--note", default="")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.complete(store_from_ctx(ctx), args.quest_id, note=args.note)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        reward = result["reward"]
        print(f"Completed quest: {result['quest']['title']}")
        print(f"Reward: +{reward['xp']} XP, +{reward['tokens']} tokens")
    return 0
