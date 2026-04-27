"""Game.DST.Snapshot.read skill.

Read the RohBridge DST snapshot JSON and return a compact, model-friendly
summary of the current game state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from Core.NSPL.File.read import read_text


DEFAULT_SNAPSHOT_PATH = (
    "~/.klei/DoNotStarveTogether/42802241/Cluster_4/Master/save/roh_dst_snapshot.json"
)


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--path",
        dest="path",
        default=DEFAULT_SNAPSHOT_PATH,
        help="Path to roh_dst_snapshot.json",
    )
    parser.add_argument(
        "--raw",
        dest="raw",
        action="store_true",
        help="Print the raw snapshot JSON instead of a summarized payload",
    )


def _summarize_player(player: Dict[str, Any]) -> Dict[str, Any]:
    position = player.get("position", {})
    if not isinstance(position, dict):
        position = {}

    return {
        "userid": str(player.get("userid", "unknown")),
        "name": str(player.get("name", "unknown")),
        "prefab": str(player.get("prefab", "unknown")),
        "is_ghost": bool(player.get("is_ghost", False)),
        "position": {
            "x": position.get("x"),
            "z": position.get("z"),
        },
    }


def _build_summary(snapshot: Dict[str, Any], path: str) -> Dict[str, Any]:
    world = snapshot.get("world", {})
    if not isinstance(world, dict):
        world = {}

    players_raw = snapshot.get("players", [])
    players: List[Dict[str, Any]] = []
    if isinstance(players_raw, list):
        for player in players_raw:
            if isinstance(player, dict):
                players.append(_summarize_player(player))

    phase = str(world.get("phase", "unknown"))
    season = str(world.get("season", "unknown"))

    signals: List[str] = []

    if phase == "night":
        signals.append("night_started_or_active")
    elif phase == "dusk":
        signals.append("dusk_active")
    elif phase == "day":
        signals.append("day_active")

    if bool(world.get("is_raining", False)):
        signals.append("raining")

    if bool(world.get("is_snowing", False)):
        signals.append("snowing")

    if any(player.get("is_ghost") for player in players):
        signals.append("player_ghost_detected")

    return {
        "ok": True,
        "source": "RohBridge",
        "path": str(Path(path).expanduser()),
        "schema_version": snapshot.get("schema_version"),
        "run_id": snapshot.get("run_id"),
        "side": snapshot.get("side"),
        "world": {
            "day": world.get("day"),
            "season": season,
            "phase": phase,
            "is_raining": bool(world.get("is_raining", False)),
            "is_snowing": bool(world.get("is_snowing", False)),
        },
        "players": players,
        "player_count": len(players),
        "signals": signals,
        "director_hint": _build_director_hint(phase, players, signals),
    }


def _build_director_hint(
    phase: str,
    players: List[Dict[str, Any]],
    signals: List[str],
) -> str:
    if "player_ghost_detected" in signals:
        return "A player is a ghost. Consider commenting, warning, or offering a recovery objective."

    if phase == "night":
        return "Night is active. Consider a short atmospheric comment or wait if players are stable."

    if phase == "dusk":
        return "Dusk is active. Consider reminding players to prepare for night."

    if len(players) == 0:
        return "No active players detected. Wait."

    return "No urgent signal detected. Wait unless there is a new objective or human note."


def run(args: argparse.Namespace, ctx: Any) -> int:
    path = str(getattr(args, "path", DEFAULT_SNAPSHOT_PATH) or DEFAULT_SNAPSHOT_PATH)

    try:
        raw = read_text(path)
        start_index = raw.find("{")
        if start_index < 0:
            raise ValueError("Snapshot file does not contain a JSON object.")

        snapshot = json.loads(raw[start_index:])
        if not isinstance(snapshot, dict):
            raise ValueError("Snapshot JSON root must be an object.")

        if bool(getattr(args, "raw", False)):
            payload = snapshot
        else:
            payload = _build_summary(snapshot, path)

        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        return 0

    except Exception as exc:
        error_payload = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(path).expanduser()),
        }

        if getattr(ctx, "json", False):
            print(json.dumps(error_payload, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)

        return 1
