from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.detail(store_from_ctx(ctx), args.quest_id)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        quest = result["quest"]
        print(f"{quest.get('title')} [{quest.get('project', 'General')} / {quest.get('category')}]")
        print(f"Status: {quest.get('status')}")
        print(f"Sessions: {len(result.get('sessions', []))}")
    return 0
