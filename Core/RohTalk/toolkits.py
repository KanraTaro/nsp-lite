"""Tool kit definitions for RohTalk.

This module owns the model-facing tool definitions and SkillCLI mapping
for named tool kits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from Core.Game.DST.commands import (
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
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
]

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
    ]


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
            skill_name_map=build_tool_name_map(DST_DIRECTOR_SKILL_NAMES),
        )

    raise ValueError(f"Unknown RohTalk toolkit: {name}")
