from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", default="Build")
    parser.add_argument("--project", default="General")
    parser.add_argument("--minimum-win", default="")
    parser.add_argument("--priority", default="3")
    parser.add_argument("--energy-cost", default="1")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.create_simple(
        store_from_ctx(ctx),
        args.title,
        category=args.category,
        project=args.project,
        minimum_win=args.minimum_win,
        priority=args.priority,
        energy_cost=args.energy_cost,
    )
    print(json.dumps({"quest": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Created quest: {result.get('title')}")
    return 0
