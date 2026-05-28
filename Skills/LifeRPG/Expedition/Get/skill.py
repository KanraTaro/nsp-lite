from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import expedition
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace, ctx: Any) -> int:
    items = expedition.active_expeditions(store_from_ctx(ctx))
    if ctx.json:
        print(json.dumps({"expeditions": items}, separators=(",", ":"), sort_keys=True))
    else:
        for item in items:
            print(f"{item['id']}\t{item.get('status')}\tprogress={item.get('progress', 0)}")
    return 0
