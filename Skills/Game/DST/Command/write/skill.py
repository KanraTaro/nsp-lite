"""Game.DST.Command.write skill.

Write safe RohBridge DST command payloads.

Supported command types:
- announce_text
- grant_reward_item
- set_objective
- set_objective_collect_item
- clear_objective
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from Core.Game.DST.commands import (
    ACCEPTED_COMMAND_TYPES,
    build_announce_text_command,
    build_clear_objective_command,
    build_collect_objective_command,
    clamp_positive_int,
    clean_text,
    validate_command_type,
)
from Core.Game.DST.paths import resolve_command_path
from Core.NSPL.File.write import write_json


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--type",
        dest="command_type",
        required=True,
        choices=sorted(ACCEPTED_COMMAND_TYPES),
        help="RohBridge command type",
    )
    parser.add_argument("--text", dest="text", default="", help="Text for announce/objective commands")
    parser.add_argument("--title", dest="title", default="", help="Objective title")
    parser.add_argument("--prefab", dest="prefab", default="", help="Prefab for reward commands")
    parser.add_argument("--count", dest="count", type=int, default=1, help="Item/reward count")
    parser.add_argument("--target-userid", dest="target_userid", default="", help="Target DST userid")
    parser.add_argument("--target-prefab", dest="target_prefab", default="", help="Objective target prefab")
    parser.add_argument("--target-count", dest="target_count", type=int, default=1, help="Objective target count")
    parser.add_argument("--reward-prefab", dest="reward_prefab", default="cutgrass", help="Objective reward prefab")
    parser.add_argument("--reward-count", dest="reward_count", type=int, default=3, help="Objective reward count")
    parser.add_argument(
        "--path",
        dest="path",
        default=None,
        help="Override path to roh_dst_command.json",
    )


def _build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    command_type = validate_command_type(args.command_type)

    if command_type == "announce_text":
        return build_announce_text_command(args.text)

    if command_type == "grant_reward_item":
        prefab = clean_text(args.prefab)
        if prefab == "":
            raise ValueError("grant_reward_item requires --prefab.")

        return {
            "type": "grant_reward_item",
            "payload": {
                "prefab": prefab,
                "count": clamp_positive_int(args.count),
                "target_userid": clean_text(args.target_userid),
            },
        }

    if command_type == "set_objective":
        title = clean_text(args.title) or "Objective"
        text = clean_text(args.text)

        return {
            "type": "set_objective",
            "payload": {
                "title": title,
                "text": text,
            },
        }

    if command_type == "set_objective_collect_item":
        if clean_text(args.target_prefab) == "":
            raise ValueError("set_objective_collect_item requires --target-prefab.")

        return build_collect_objective_command(
            args.title,
            args.text,
            args.target_prefab,
            args.target_count,
            args.reward_prefab,
            args.reward_count,
            args.target_userid,
        )

    if command_type == "clear_objective":
        return build_clear_objective_command()

    raise ValueError(f"Unsupported command type: {command_type}")


def run(args: argparse.Namespace, ctx: Any) -> int:
    path = str(Path(getattr(args, "path", "") or "roh_dst_command.json").expanduser())

    try:
        explicit_path = getattr(args, "path", None)
        path = str(Path(explicit_path).expanduser()) if explicit_path else str(resolve_command_path())
        payload = _build_payload(args)
        written_path = write_json(path, payload)

        result = {
            "ok": True,
            "path": str(Path(written_path).expanduser()),
            "command": payload,
        }

        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0

    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(path).expanduser()),
        }

        if getattr(ctx, "json", False):
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)

        return 1
