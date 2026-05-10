"""Game.DST.Announce.text skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from Core.Game.DST.commands import build_announce_text_command
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", dest="text", required=True, help="Announcement text")
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        payload = build_announce_text_command(args.text)
    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(getattr(args, "path", "") or "roh_dst_command.json").expanduser()),
        }
        if getattr(ctx, "json", False):
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)
        return 1

    return write_command_payload(args, ctx, payload)
