from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import habits
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace, ctx: Any) -> int:
    items = habits.list_habits(store_from_ctx(ctx))
    if ctx.json:
        print(json.dumps({"habits": items}, separators=(",", ":"), sort_keys=True))
    else:
        for habit in items:
            print(f"{habit['id']}\t{habit.get('status')}\t{habit.get('title')}\tstreak={habit.get('streak', 0)}")
    return 0
