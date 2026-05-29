from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import settings
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace, ctx: Any) -> int:
    result = settings.get_settings(store_from_ctx(ctx))
    print(json.dumps({"settings": result}, separators=(",", ":"), sort_keys=True) if ctx.json else f"LifeRPG settings for {result.get('display_name')}")
    return 0
