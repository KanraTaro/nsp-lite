"""Tool kit definitions for RohTalk.

This module owns the model-facing tool definitions and SkillCLI mapping
for named tool kits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from Core.Game.DST.commands import (
    MODEL_SAFE_COMMAND_TYPES,
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
    "Game.DST.Command.write",
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
    
    
def _dst_command_tool() -> ToolDef:
    return ToolDef(
        name=canonical_skill_name_to_tool_name("Game.DST.Command.write"),
        description=(
            "Issue a Don't Starve Together director command. "
            "Use this to affect the game world. "
            "Prefer small, meaningful actions. Do not spam.\n\n"
            "Common uses:\n"
            "- announce_text → send a message to players\n"
            "- set_objective_collect_item → create a small task\n"
            "- clear_objective → remove current task\n\n"
            "Safe prefabs: log, cutgrass, twigs, flint, silk, goldnugget."
        ),
        parameters={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": list(MODEL_SAFE_COMMAND_TYPES),
                },
                "text": {"type": "string"},
                "title": {"type": "string"},
                "target_prefab": {
                    "type": "string",
                    "enum": list(SAFE_COLLECT_PREFABS),
                },
                "target_count": {"type": "integer", "minimum": 1},
                "reward_prefab": {
                    "type": "string",
                    "enum": list(SAFE_REWARD_PREFABS),
                },
                "reward_count": {"type": "integer", "minimum": 1},
                "target_userid": {"type": "string"},
            },
            "required": ["type"],
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
        _dst_command_tool(),
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
