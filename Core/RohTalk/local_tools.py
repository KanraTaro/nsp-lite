"""Shared local tools for RohTalk.

This module defines a small in-process tool set for RohTalk.

Design intent:
- remove duplication across temporary tool-enabled entrypoints
- provide a lightweight local fallback/bootstrapping tool source
- remain secondary to the long-term SkillCLI-backed execution path

These tools are intentionally simple and local. They are useful for:
- tests
- smoke checks
- proving flows
- fallback execution when SkillCLI-backed tools are not yet in place
"""

from __future__ import annotations

from typing import Any, Dict, List

from Core.LLMClient.types import ToolDef


def get_weather(city: str) -> Dict[str, Any]:
    """Return a fake weather payload for proving tool-loop behavior."""
    return {
        "city": city,
        "forecast": "Partly cloudy",
        "temp_f": 82,
    }


LOCAL_TOOLS: List[ToolDef] = [
    ToolDef(
        name="get_weather",
        description="Get the weather for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
            },
            "required": ["city"],
        },
    )
]


LOCAL_TOOL_IMPL = {
    "get_weather": get_weather,
}
