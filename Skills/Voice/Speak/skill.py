from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from Core.Voice.speechnote import check_speechnote, speak_speechnote


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", dest="text", default="", help="Text to speak")
    parser.add_argument(
        "--provider",
        dest="provider",
        default="speechnote",
        choices=["speechnote"],
        help="Voice provider to use",
    )
    parser.add_argument("--check", dest="check", action="store_true", help="Check provider availability without speaking")


def _emit(payload: Dict[str, Any], ctx: Any) -> None:
    if getattr(ctx, "json", False):
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        return

    if bool(payload.get("ok")):
        print(str(payload.get("message") or "Voice provider is available."))
        return

    print(str(payload.get("stderr") or payload.get("error") or "Voice provider failed."), file=sys.stderr)


def run(args: argparse.Namespace, ctx: Any) -> int:
    provider = str(getattr(args, "provider", "speechnote") or "speechnote").strip().lower()
    if provider != "speechnote":
        payload = {
            "ok": False,
            "provider": provider,
            "exit_code": 2,
            "stderr": f"unsupported voice provider: {provider}",
        }
        _emit(payload, ctx)
        return 2

    if bool(getattr(args, "check", False)):
        payload = check_speechnote()
    else:
        payload = speak_speechnote(str(getattr(args, "text", "") or ""))

    _emit(payload, ctx)
    return 0 if bool(payload.get("ok")) else int(payload.get("exit_code", 1) or 1)
