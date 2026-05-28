from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import inbox
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", required=True, help="Messy task text to capture")


def run(args: argparse.Namespace, ctx: Any) -> int:
    items = inbox.add_text(store_from_ctx(ctx), args.text)
    if ctx.json:
        print(json.dumps({"items": items}, separators=(",", ":"), sort_keys=True))
    else:
        print(f"Captured {len(items)} inbox item(s).")
        for item in items:
            print(f"- {item['original_text']}")
    return 0
