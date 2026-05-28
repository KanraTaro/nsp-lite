from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import habits
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--habit-id", required=True)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = habits.check(store_from_ctx(ctx), args.habit_id)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        reward = result["reward"]
        print(f"Checked habit: {result['habit']['title']} (+{reward['xp']} XP, +{reward['tokens']} token)")
    return 0
