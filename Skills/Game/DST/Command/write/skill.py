"""Game.DST.Command.write skill.

Write safe RohBridge DST command payloads.

Supported command types:
- announce_text
- grant_reward_item
- set_objective
- set_objective_collect_item
- clear_objective
- set_chaos_tier
- spawn_supplies
- spawn_enemy
- trigger_event
- clear_spawned_enemies
- clear_spawned_bosses
- set_player_objective_collect_item
- clear_player_objective
- objective_status
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
    build_clear_player_objective_command,
    build_clear_objective_command,
    build_clear_spawned_bosses_command,
    build_clear_spawned_enemies_command,
    build_collect_objective_command,
    build_objective_status_command,
    build_player_collect_objective_command,
    build_set_chaos_tier_command,
    build_spawn_enemy_command,
    build_spawn_supplies_command,
    build_trigger_event_command,
    clamp_positive_int,
    clean_text,
    validate_command_type,
)
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


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
    parser.add_argument("--chaos-tier", dest="chaos_tier", type=int, default=1, help="Chaos tier 0-3")
    parser.add_argument("--target-mode", dest="target_mode", default="first", help="Player targeting mode")
    parser.add_argument("--radius", dest="radius", type=int, default=8, help="Spawn/event radius")
    parser.add_argument("--event-name", dest="event_name", default="", help="Chaos event name")
    parser.add_argument("--intensity", dest="intensity", type=int, default=1, help="Event intensity")
    parser.add_argument("--duration-seconds", dest="duration_seconds", type=int, default=20, help="Event duration")
    parser.add_argument("--announce", dest="announce", default="", help="Announcement text for flat RohBridge commands")
    parser.add_argument("--announce-objective", dest="announce_objective", action="store_true", default=True, help="Announce objective commands")
    parser.add_argument("--no-announce-objective", dest="announce_objective", action="store_false", help="Do not announce objective commands")
    parser.add_argument("--force-boss", dest="force_boss", action="store_true", help="Required for deerclops boss spawning")
    parser.add_argument("--all", dest="all", action="store_true", default=True, help="Request all objective statuses")
    add_transport_args(parser, path_help="Override path to roh_dst_command.json")


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

    if command_type == "set_chaos_tier":
        return build_set_chaos_tier_command(args.chaos_tier, args.announce)

    if command_type == "spawn_supplies":
        return build_spawn_supplies_command(
            args.prefab,
            args.count,
            args.target_mode,
            args.radius,
            args.announce,
        )

    if command_type == "spawn_enemy":
        return build_spawn_enemy_command(
            args.prefab,
            args.count,
            args.target_mode,
            args.radius,
            args.announce,
            args.force_boss,
        )

    if command_type == "trigger_event":
        return build_trigger_event_command(
            args.event_name,
            args.target_mode,
            args.intensity,
            args.duration_seconds,
            args.radius,
            args.announce,
        )

    if command_type == "clear_spawned_enemies":
        return build_clear_spawned_enemies_command(args.announce)

    if command_type == "clear_spawned_bosses":
        return build_clear_spawned_bosses_command(args.announce)

    if command_type == "set_player_objective_collect_item":
        return build_player_collect_objective_command(
            args.title,
            args.text,
            args.target_prefab,
            args.target_count,
            args.reward_prefab,
            args.reward_count,
            args.target_userid,
            args.target_mode,
            args.announce_objective,
        )

    if command_type == "clear_player_objective":
        return build_clear_player_objective_command(
            args.target_userid,
            args.target_mode,
            args.announce_objective,
        )

    if command_type == "objective_status":
        return build_objective_status_command(args.all)

    raise ValueError(f"Unsupported command type: {command_type}")


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        payload = _build_payload(args)
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
