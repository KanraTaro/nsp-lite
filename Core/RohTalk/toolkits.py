"""Tool kit definitions for RohTalk.

This module owns the model-facing tool definitions and SkillCLI mapping
for named tool kits.

Current scope:
- keep the first tool kit simple and explicit
- make it easy to add Scanner/File/DST/media tool kits later
- keep orchestrator.py focused on running turns, not defining tools
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

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


def _basic_tools() -> List[ToolDef]:
    return [
        ToolDef(
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
        ),
        ToolDef(
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
        ),
    ]


def resolve_toolkit(name: str = "basic") -> ToolKit:
    """Resolve a named RohTalk tool kit.

    Supported tool kits:
    - basic: weather + time proving tools
    """
    normalized = str(name or "basic").strip().lower()

    if normalized == "basic":
        return ToolKit(
            name="basic",
            tools=_basic_tools(),
            skill_name_map=build_tool_name_map(BASIC_SKILL_NAMES),
        )

    raise ValueError(f"Unknown RohTalk toolkit: {name}")
