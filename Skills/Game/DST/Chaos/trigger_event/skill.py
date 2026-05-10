"""Game.DST.Chaos.trigger_event skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import (
    SAFE_EVENT_NAMES,
    TARGET_MODES,
    build_trigger_event_command,
)
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--event-name", dest="event_name", required=True, choices=SAFE_EVENT_NAMES, help="Chaos event name")
    parser.add_argument("--target-mode", dest="target_mode", default="first", choices=TARGET_MODES, help="Player targeting mode")
    parser.add_argument("--intensity", dest="intensity", type=int, default=1, help="Event intensity")
    parser.add_argument("--duration-seconds", dest="duration_seconds", type=int, default=20, help="Event duration")
    parser.add_argument("--radius", dest="radius", type=int, default=10, help="Event radius")
    parser.add_argument("--announce", dest="announce", default="", help="Optional in-game announcement")
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_trigger_event_command(
        args.event_name,
        args.target_mode,
        args.intensity,
        args.duration_seconds,
        args.radius,
        args.announce,
    )
    return write_command_payload(args, ctx, payload)
