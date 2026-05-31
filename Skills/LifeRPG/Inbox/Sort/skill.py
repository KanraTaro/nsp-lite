from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import sorting
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", default="raw")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = sorting.sort_inbox(store_from_ctx(ctx), status=args.status)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        print(f"Roh sorted {len(result['items'])} item(s).")
        for item in result["items"]:
            print(f"- [{item.get('project', 'General')} / {item['category']}] {item['title']} | win: {item['minimum_win']}")
    return 0
