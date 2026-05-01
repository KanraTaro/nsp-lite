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
    clamp_positive_int,
    clamp_reward_count,
    validate_collect_prefab,
    validate_command_type,
    validate_reward_prefab,
)
from Core.NSPL.File.write import write_json


DEFAULT_COMMAND_PATH = (
    "~/.klei/DoNotStarveTogether/42802241/Cluster_4/Master/save/roh_dst_command.json"
)

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
        default=DEFAULT_COMMAND_PATH,
        help="Path to roh_dst_command.json",
    )


def _clean_text(value: str) -> str:
    return str(value or "").strip()


def _build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    command_type = validate_command_type(args.command_type)

    if command_type == "announce_text":
        text = _clean_text(args.text)
        if text == "":
            raise ValueError("announce_text requires --text.")

        return {
            "type": "announce_text",
            "payload": {
                "text": text,
            },
        }

    if command_type == "grant_reward_item":
        prefab = _clean_text(args.prefab)
        if prefab == "":
            raise ValueError("grant_reward_item requires --prefab.")

        return {
            "type": "grant_reward_item",
            "payload": {
                "prefab": prefab,
                "count": clamp_positive_int(args.count),
                "target_userid": _clean_text(args.target_userid),
            },
        }

    if command_type == "set_objective":
        title = _clean_text(args.title) or "Objective"
        text = _clean_text(args.text)

        return {
            "type": "set_objective",
            "payload": {
                "title": title,
                "text": text,
            },
        }

    if command_type == "set_objective_collect_item":
        title = _clean_text(args.title) or "Objective"
        text = _clean_text(args.text)
        raw_target_prefab = _clean_text(args.target_prefab)
        reward_prefab = validate_reward_prefab(_clean_text(args.reward_prefab) or "cutgrass")

        if raw_target_prefab == "":
            raise ValueError("set_objective_collect_item requires --target-prefab.")

        target_prefab = validate_collect_prefab(raw_target_prefab)

        return {
            "type": "set_objective_collect_item",
            "payload": {
                "title": title,
                "text": text,
                "target_userid": _clean_text(args.target_userid),
                "target_prefab": target_prefab,
                "target_count": clamp_positive_int(args.target_count),
                "reward_prefab": reward_prefab,
                "reward_count": clamp_reward_count(reward_prefab, args.reward_count),
            },
        }

    if command_type == "clear_objective":
        return {
            "type": "clear_objective",
            "payload": {},
        }

    raise ValueError(f"Unsupported command type: {command_type}")


def run(args: argparse.Namespace, ctx: Any) -> int:
    path = str(getattr(args, "path", DEFAULT_COMMAND_PATH) or DEFAULT_COMMAND_PATH)

    try:
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
