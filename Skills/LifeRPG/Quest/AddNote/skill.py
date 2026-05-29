from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import quests
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--quest-id", required=True)
    parser.add_argument("--note", required=True)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = quests.add_note(store_from_ctx(ctx), args.quest_id, args.note)
    print(json.dumps(result, separators=(",", ":"), sort_keys=True) if ctx.json else "Added quest note.")
    return 0
