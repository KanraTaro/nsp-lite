from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import inbox
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    items = inbox.list_items(store_from_ctx(ctx), status=args.status)
    if ctx.json:
        print(json.dumps({"items": items}, separators=(",", ":"), sort_keys=True))
    else:
        for item in items:
            print(f"{item['id']}\t{item.get('status')}\t{item.get('title') or item.get('original_text')}")
    return 0
