from __future__ import annotations

import argparse
import json
from typing import Any

from Core.LifeRPG.services import missions
from Core.LifeRPG.store import store_from_ctx


def build_parser(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = missions.board(store_from_ctx(ctx))
    if ctx.json:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        mission = payload["mission"]
        print(f"Mission: {mission.get('title', 'No mission')}")
        active = payload.get("active")
        if active and active.get("quest"):
            print(f"Active quest: {active['quest'].get('title')}")
        print(f"XP: {payload['ledger'].get('xp_total', 0)} | Tokens: {payload['ledger'].get('leisure_tokens', 0)}")
    return 0
