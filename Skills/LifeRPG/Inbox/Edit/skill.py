from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import inbox
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--inbox-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--text", default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--minimum-win", default=None)
    parser.add_argument("--priority", default=None)
    parser.add_argument("--energy-cost", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = inbox.edit_item(
        store_from_ctx(ctx),
        args.inbox_id,
        title=args.title,
        text=args.text,
        category=args.category,
        minimum_win=args.minimum_win,
        priority=args.priority,
        energy_cost=args.energy_cost,
    )
    print(json.dumps({"item": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Edited inbox item: {result.get('title')}")
    return 0
