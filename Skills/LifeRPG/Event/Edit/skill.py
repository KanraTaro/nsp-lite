from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import events
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--starts-at", default=None)
    parser.add_argument("--ends-at", default=None)
    parser.add_argument("--reminder-minutes", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--notes", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = events.edit(
        store_from_ctx(ctx),
        args.event_id,
        title=args.title,
        starts_at=args.starts_at,
        ends_at=args.ends_at,
        reminder_minutes=args.reminder_minutes,
        status=args.status,
        notes=args.notes,
    )
    print(json.dumps({"event": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"Edited event: {result.get('title')}")
    return 0
