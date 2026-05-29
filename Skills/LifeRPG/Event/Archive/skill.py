from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import events
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--delete", action="store_true")


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = events.archive(store_from_ctx(ctx), args.event_id, delete=bool(args.delete))
    print(json.dumps({"event": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Archived event: {result.get('title')}")
    return 0
