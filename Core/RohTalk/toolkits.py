"""Tool kit definitions for RohTalk.

This module owns the model-facing tool definitions and SkillCLI mapping
for named tool kits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from Core.Game.DST.commands import (
    SAFE_ENEMY_PREFABS,
    SAFE_EVENT_NAMES,
    SAFE_SUPPLY_PREFABS,
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
    TARGET_MODES,
)
from Core.LLMClient.types import ToolDef

from .skillcli_tools import build_tool_name_map, canonical_skill_name_to_tool_name


@dataclass(frozen=True)
class ToolKit:
    """Resolved tool kit data for a tool-capable RohTalk turn."""

    name: str
    tools: List[ToolDef]
    skill_name_map: Dict[str, str]


BASIC_SKILL_NAMES: List[str] = [
    "NSPL.Tools.Weather.get",
    "NSPL.Tools.Time.now",
]

DST_DIRECTOR_SKILL_NAMES: List[str] = [
    "NSPL.Tools.Time.now",
    "Game.DST.Snapshot.read",
    "Game.DST.Announce.text",
    "Game.DST.Objective.collect",
    "Game.DST.Objective.clear",
    "Game.DST.Chaos.set_tier",
    "Game.DST.Chaos.spawn_supplies",
    "Game.DST.Chaos.spawn_enemy",
    "Game.DST.Chaos.trigger_event",
    "Game.DST.Chaos.clear_enemies",
    "Game.DST.Chaos.clear_bosses",
    "Game.DST.Objective.player_collect",
    "Game.DST.Objective.clear_player",
    "Game.DST.Objective.status",
]


DST_DIRECTOR_TOOL_ALIASES: Dict[str, str] = {
    "chaos_set_tier": "Game.DST.Chaos.set_tier",
    "supplies_spawn": "Game.DST.Chaos.spawn_supplies",
    "enemy_spawn": "Game.DST.Chaos.spawn_enemy",
    "event_trigger": "Game.DST.Chaos.trigger_event",
    "spawned_enemies_clear": "Game.DST.Chaos.clear_enemies",
    "spawned_bosses_clear": "Game.DST.Chaos.clear_bosses",
    "player_objective_collect": "Game.DST.Objective.player_collect",
    "player_objective_clear": "Game.DST.Objective.clear_player",
    "objective_status": "Game.DST.Objective.status",
}


def _time_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("NSPL.Tools.Time.now"),
        description=(
            "Get the current date and time. "
            "Use this when the user asks for the current time, date, day, or timezone-aware time."
        ),
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Optional IANA timezone name, such as America/New_York.",
                }
            },
            "required": [],
        },
    )


def _weather_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("NSPL.Tools.Weather.get"),
        description=(
            "Get the weather for a city. "
            "Use this when the user asks about weather in a specific place."
        ),
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to get weather for",
                }
            },
            "required": ["city"],
        },
    )


def _dst_snapshot_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("Game.DST.Snapshot.read"),
        description=(
            "Read the current Don't Starve Together RohBridge snapshot. "
            "Use this to inspect live game state, world phase, day, season, players, ghost status, and director hints."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    
    
def _dst_announce_text_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("Game.DST.Announce.text"),
        description=(
            "Send a short Don't Starve Together in-game director message to players. "
            "Use this for brief warnings, nudges, or acknowledgements. Do not spam."
        ),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Short in-game message text.",
                },
            },
            "required": ["text"],
        },
    )


def _dst_objective_collect_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("Game.DST.Objective.collect"),
        description=(
            "Create a safe Don't Starve Together collection objective. "
            "Use this for small recovery or supply tasks. "
            "Safe prefabs: log, cutgrass, twigs, flint, silk, goldnugget."
        ),
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "text": {"type": "string"},
                "target_prefab": {"type": "string", "enum": list(SAFE_COLLECT_PREFABS)},
                "target_count": {"type": "integer", "minimum": 1},
                "reward_prefab": {
                    "type": "string",
                    "enum": list(SAFE_REWARD_PREFABS),
                },
                "reward_count": {"type": "integer", "minimum": 1},
                "target_userid": {"type": "string"},
            },
            "required": ["target_prefab", "target_count"],
        },
    )


def _dst_objective_clear_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("Game.DST.Objective.clear"),
        description="Clear the current Don't Starve Together director objective.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


def _target_mode_property() -> Dict[str, object]:
    return {
        "type": "string",
        "enum": list(TARGET_MODES),
        "description": "Player targeting mode. Prefer first unless there is a clear reason to target another group.",
    }


def _dst_chaos_set_tier_tool() -> ToolDef:
    return ToolDef(
        name="chaos_set_tier",
        description=(
            "Set the Don't Starve Together RohBridge chaos tier. "
            "Use tier 3 before any deerclops boss workflow."
        ),
        parameters={
            "type": "object",
            "properties": {
                "chaos_tier": {"type": "integer", "enum": [0, 1, 2, 3]},
                "announce": {"type": "string"},
            },
            "required": ["chaos_tier"],
        },
    )


def _dst_supplies_spawn_tool() -> ToolDef:
    return ToolDef(
        name="supplies_spawn",
        description=(
            "Spawn an allowlisted Don't Starve Together supply prefab near a selected player. "
            "Use sparingly for recovery or pacing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "prefab": {"type": "string", "enum": list(SAFE_SUPPLY_PREFABS)},
                "count": {"type": "integer", "minimum": 1, "maximum": 20},
                "target_mode": _target_mode_property(),
                "radius": {"type": "integer", "minimum": 1, "maximum": 20},
                "announce": {"type": "string"},
            },
            "required": ["prefab"],
        },
    )


def _dst_enemy_spawn_tool() -> ToolDef:
    return ToolDef(
        name="enemy_spawn",
        description=(
            "Spawn an allowlisted Don't Starve Together enemy near a selected player. "
            "Only deerclops is allowed as a boss; use deerclops only after setting chaos tier 3 "
            "and pass force_boss=true explicitly."
        ),
        parameters={
            "type": "object",
            "properties": {
                "prefab": {"type": "string", "enum": list(SAFE_ENEMY_PREFABS)},
                "count": {"type": "integer", "minimum": 1, "maximum": 10},
                "target_mode": _target_mode_property(),
                "radius": {"type": "integer", "minimum": 1, "maximum": 30},
                "announce": {"type": "string"},
                "force_boss": {
                    "type": "boolean",
                    "description": "Required only for deerclops after chaos tier 3 has been set.",
                },
            },
            "required": ["prefab"],
        },
    )


def _dst_event_trigger_tool() -> ToolDef:
    return ToolDef(
        name="event_trigger",
        description="Trigger an allowlisted RohBridge chaos event such as light or medium frog rain.",
        parameters={
            "type": "object",
            "properties": {
                "event_name": {"type": "string", "enum": list(SAFE_EVENT_NAMES)},
                "target_mode": _target_mode_property(),
                "intensity": {"type": "integer", "minimum": 1, "maximum": 3},
                "duration_seconds": {"type": "integer", "minimum": 5, "maximum": 120},
                "radius": {"type": "integer", "minimum": 1, "maximum": 30},
                "announce": {"type": "string"},
            },
            "required": ["event_name"],
        },
    )


def _dst_spawned_enemies_clear_tool() -> ToolDef:
    return ToolDef(
        name="spawned_enemies_clear",
        description="Clear only RohBridge-tracked spawned enemies, not naturally spawned mobs.",
        parameters={
            "type": "object",
            "properties": {"announce": {"type": "string"}},
            "required": [],
        },
    )


def _dst_spawned_bosses_clear_tool() -> ToolDef:
    return ToolDef(
        name="spawned_bosses_clear",
        description="Clear only RohBridge-tracked spawned bosses, not naturally spawned mobs.",
        parameters={
            "type": "object",
            "properties": {"announce": {"type": "string"}},
            "required": [],
        },
    )


def _dst_player_objective_collect_tool() -> ToolDef:
    return ToolDef(
        name="player_objective_collect",
        description=(
            "Create a per-player Don't Starve Together collection objective. "
            "Use target_userid when known; otherwise use target_mode."
        ),
        parameters={
            "type": "object",
            "properties": {
                "target_userid": {"type": "string"},
                "target_mode": _target_mode_property(),
                "title": {"type": "string"},
                "text": {"type": "string"},
                "target_prefab": {"type": "string", "enum": list(SAFE_COLLECT_PREFABS)},
                "target_count": {"type": "integer", "minimum": 1},
                "reward_prefab": {"type": "string", "enum": list(SAFE_REWARD_PREFABS)},
                "reward_count": {"type": "integer", "minimum": 1},
                "announce": {"type": "boolean"},
            },
            "required": ["target_prefab", "target_count"],
        },
    )


def _dst_player_objective_clear_tool() -> ToolDef:
    return ToolDef(
        name="player_objective_clear",
        description="Clear a per-player Don't Starve Together objective by userid or target mode.",
        parameters={
            "type": "object",
            "properties": {
                "target_userid": {"type": "string"},
                "target_mode": _target_mode_property(),
                "announce": {"type": "boolean"},
            },
            "required": [],
        },
    )


def _dst_objective_status_tool() -> ToolDef:
    return ToolDef(
        name="objective_status",
        description="Request RohBridge objective status for active objectives.",
        parameters={
            "type": "object",
            "properties": {
                "all": {"type": "boolean"},
            },
            "required": [],
        },
    )


def _basic_tools() -> List[ToolDef]:
    return [
        _weather_tool(),
        _time_tool(),
    ]


def _dst_director_tools() -> List[ToolDef]:
    return [
        _time_tool(),
        _dst_snapshot_tool(),
        _dst_announce_text_tool(),
        _dst_objective_collect_tool(),
        _dst_objective_clear_tool(),
        _dst_chaos_set_tier_tool(),
        _dst_supplies_spawn_tool(),
        _dst_enemy_spawn_tool(),
        _dst_event_trigger_tool(),
        _dst_spawned_enemies_clear_tool(),
        _dst_spawned_bosses_clear_tool(),
        _dst_player_objective_collect_tool(),
        _dst_player_objective_clear_tool(),
        _dst_objective_status_tool(),
    ]


def _dst_director_skill_name_map() -> Dict[str, str]:
    mapping = build_tool_name_map(DST_DIRECTOR_SKILL_NAMES)
    mapping.update(DST_DIRECTOR_TOOL_ALIASES)
    return mapping


def resolve_toolkit(name: str = "basic") -> ToolKit:
    """Resolve a named RohTalk tool kit.

    Supported tool kits:
    - basic: weather + time proving tools
    - dst_director: time + DST snapshot reader
    """
    normalized = str(name or "basic").strip().lower()

    if normalized == "basic":
        return ToolKit(
            name="basic",
            tools=_basic_tools(),
            skill_name_map=build_tool_name_map(BASIC_SKILL_NAMES),
        )

    if normalized in {"dst", "dst_director", "game_dst"}:
        return ToolKit(
            name="dst_director",
            tools=_dst_director_tools(),
            skill_name_map=_dst_director_skill_name_map(),
        )

    raise ValueError(f"Unknown RohTalk toolkit: {name}")
