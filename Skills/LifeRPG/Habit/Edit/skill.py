from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import habits
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--habit-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--cadence", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = habits.edit(store_from_ctx(ctx), args.habit_id, title=args.title, category=args.category, cadence=args.cadence)
    print(json.dumps({"habit": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Edited habit: {result.get('title')}")
    return 0
