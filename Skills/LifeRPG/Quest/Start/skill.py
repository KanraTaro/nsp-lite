from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--quest-id")
    group.add_argument("--inbox-id")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.start(store_from_ctx(ctx), quest_id=args.quest_id, inbox_id=args.inbox_id)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        print(f"Started quest: {result['quest']['title']}")
        print(f"Session: {result['session']['id']}")
        print(f"Expedition: {result['expedition']['id']}")
    return 0
