from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    items = quests.list_quests(store_from_ctx(ctx), status=args.status)
    if ctx.json:
        print(json.dumps({"quests": items}, separators=(",", ":"), sort_keys=True))
    else:
        for quest in items:
            print(f"{quest['id']}\t{quest.get('status')}\t[{quest.get('project', 'General')} / {quest.get('category')}] {quest.get('title')}")
    return 0
