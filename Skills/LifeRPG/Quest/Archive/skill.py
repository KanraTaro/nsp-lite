from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--delete", action="store_true")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.archive_quest(store_from_ctx(ctx), args.quest_id, delete=bool(args.delete))
    print(json.dumps({"quest": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Archived quest: {result.get('title')}")
    return 0
