from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import expedition
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expedition-id", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = expedition.tick(store_from_ctx(ctx), expedition_id=args.expedition_id)
    if ctx.json:
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        print(f"Expedition {result['id']}: {result.get('progress', 0)}%")
        if result.get("log"):
            print(result["log"][-1])
    return 0
