from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import habits
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", default="Body")
    parser.add_argument("--cadence", default="daily")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = habits.create(store_from_ctx(ctx), args.title, category=args.category, cadence=args.cadence)
    print(json.dumps({"habit": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Created habit: {result.get('title')}")
    return 0
