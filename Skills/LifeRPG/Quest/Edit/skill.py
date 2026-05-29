from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--minimum-win", default=None)
    parser.add_argument("--priority", default=None)
    parser.add_argument("--energy-cost", default=None)
    parser.add_argument("--status", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.edit_quest(
        store_from_ctx(ctx),
        args.quest_id,
        title=args.title,
        category=args.category,
        minimum_win=args.minimum_win,
        priority=args.priority,
        energy_cost=args.energy_cost,
        status=args.status,
    )
    print(json.dumps({"quest": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Edited quest: {result.get('title')}")
    return 0
