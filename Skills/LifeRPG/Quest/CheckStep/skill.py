from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--step-id", required=True)
    parser.add_argument("--status", default="completed")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.check_step(store_from_ctx(ctx), args.quest_id, args.step_id, status=args.status)
    print(json.dumps(result, separators=(",", ":"), sort_keys=True) if ctx.json else f"Updated step: {result['step'].get('title')}")
    return 0
