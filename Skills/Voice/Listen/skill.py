from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from Core.Voice.speechnote import listen_speechnote_clipboard


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider",
        dest="provider",
        default="speechnote",
        choices=["speechnote"],
        help="Voice provider to use",
    )
    parser.add_argument("--timeout", dest="timeout", type=float, default=20.0, help="Listen timeout in seconds")
    parser.add_argument(
        "--allow-unchanged",
        dest="require_change",
        action="store_false",
        help="Allow returning the current clipboard value even if SpeechNote did not change it",
    )
    parser.set_defaults(require_change=True)
    parser.add_argument(
        "--poll-interval",
        dest="poll_interval",
        type=float,
        default=0.25,
        help="Clipboard polling interval in seconds",
    )


def _emit(payload: Dict[str, Any], ctx: Any) -> None:
    if getattr(ctx, "json", False):
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        return

    if bool(payload.get("ok")):
        print(str(payload.get("transcript", "") or ""))
        return

    print(str(payload.get("error") or payload.get("stderr") or "Voice listen failed."), file=sys.stderr)


def run(args: argparse.Namespace, ctx: Any) -> int:
    provider = str(getattr(args, "provider", "speechnote") or "speechnote").strip().lower()
    if provider != "speechnote":
        payload = {
            "ok": False,
            "provider": provider,
            "transcript": "",
            "method": "clipboard",
            "error": f"unsupported voice provider: {provider}",
            "exit_code": 2,
        }
        _emit(payload, ctx)
        return 2

    payload = listen_speechnote_clipboard(
        timeout=float(getattr(args, "timeout", 20.0) or 20.0),
        require_change=bool(getattr(args, "require_change", True)),
        poll_interval=float(getattr(args, "poll_interval", 0.25) or 0.25),
    )
    _emit(payload, ctx)
    return 0 if bool(payload.get("ok")) else int(payload.get("exit_code", 1) or 1)
