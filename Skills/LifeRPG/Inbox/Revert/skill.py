from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import sorting
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--inbox-id", required=True)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = sorting.revert_item(store_from_ctx(ctx), args.inbox_id)
    print(json.dumps({"item": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Reverted inbox item: {result.get('original_text')}")
    return 0
