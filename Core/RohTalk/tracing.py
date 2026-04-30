"""Console tracing helpers for RohTalk tool-capable turns.

This module provides small reusable callbacks for displaying tool-loop
activity in CLI skills.

Design intent:
- keep tool-loop tracing formatting consistent across skills
- avoid duplicating callback printers in AutoRoh, shell, tool_test, etc.
- keep tracing optional and caller-controlled
- preserve RohTalk core callback contracts without coupling to any one skill

These helpers are intentionally console-oriented. Future WebGUI support
should use the same event concepts, but likely emit structured events
instead of printing directly.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, TextIO


def print_step(step_index: int, *, stream: TextIO | None = None) -> None:
    """Print a model/tool-loop step marker.

    ``step_index`` is zero-based because that is what run_tool_loop emits.
    The displayed value is one-based for human readability.
    """
    output = stream or sys.stderr
    print(f"[step {step_index + 1}]", file=output)


def print_tool_call(tool_call: Any, *, stream: TextIO | None = None) -> None:
    """Print a normalized model-requested tool call."""
    output = stream or sys.stderr
    name = str(getattr(tool_call, "name", "") or "")
    arguments = getattr(tool_call, "arguments", {})

    if not isinstance(arguments, dict):
        arguments = {}

    print(
        f"[tool_call] {name} "
        f"{json.dumps(arguments, separators=(',', ':'), sort_keys=True)}",
        file=output,
    )


def print_tool_result(tool_result: Dict[str, Any], *, stream: TextIO | None = None) -> None:
    """Print a normalized tool execution result."""
    output = stream or sys.stderr

    print(
        f"[tool_result] {json.dumps(tool_result, separators=(',', ':'), sort_keys=True)}",
        file=output,
    )
