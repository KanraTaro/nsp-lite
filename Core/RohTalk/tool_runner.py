"""Tool execution helpers for RohTalk.

This module provides the execution seam for RohTalk tool calls.

Current role:
- accept a normalized tool call
- resolve the tool by name from an injected implementation map
- execute it safely
- return a normalized result payload that the tool loop can always
  append back into conversation history

Design intent:
- long term, tool execution should resolve through SkillCLI so that
  human, agent, and automation-triggered tool usage all share the same
  execution surface
- the tool loop should not care whether a tool was executed via a
  direct Python callable, SkillCLI, or another adapter
- this module is the seam that allows that implementation to evolve
  without changing tool loop behavior
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from Core.LLMClient.types import ToolCall


ToolImplMap = Mapping[str, Callable[..., Any]]


def execute_tool_call(
    tool_call: ToolCall,
    tool_impl: ToolImplMap,
) -> Dict[str, Any]:
    """Execute a normalized tool call and return a normalized result payload.

    The returned dictionary is always safe to serialize and append as a
    tool result message in conversation history.

    Success shape:
    {
      "ok": True,
      "tool_name": "...",
      "tool_call_id": "...",
      "result": <tool output>
    }

    Failure shape:
    {
      "ok": False,
      "tool_name": "...",
      "tool_call_id": "...",
      "error": "..."
    }
    """
    tool_name = str(tool_call.name or "").strip()
    tool_call_id = str(tool_call.id or "").strip()

    if tool_name == "":
        return {
            "ok": False,
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "error": "Tool call is missing a tool name.",
        }

    fn = tool_impl.get(tool_name)
    if fn is None:
        return {
            "ok": False,
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "error": f"Unknown tool: {tool_name}",
        }

    try:
        result = fn(**tool_call.arguments)
    except Exception as exc:
        return {
            "ok": False,
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "error": str(exc),
        }

    return {
        "ok": True,
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "result": result,
    }
