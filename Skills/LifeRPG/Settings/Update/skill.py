from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import settings
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--timezone", default=None)
    parser.add_argument("--auto-sort-enabled", default=None)
    parser.add_argument("--checkin-minutes", default=None)
    parser.add_argument("--reward-intensity", default=None)
    parser.add_argument("--strictness-mode", default=None)
    parser.add_argument("--visual-mode", default=None)


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = settings.update_settings(
        store_from_ctx(ctx),
        display_name=args.display_name,
        timezone=args.timezone,
        auto_sort_enabled=args.auto_sort_enabled,
        checkin_minutes=args.checkin_minutes,
        reward_intensity=args.reward_intensity,
        strictness_mode=args.strictness_mode,
        visual_mode=args.visual_mode,
    )
    print(json.dumps({"settings": result}, separators=(",", ":"), sort_keys=True) if ctx.json else "Saved LifeRPG settings.")
    return 0
