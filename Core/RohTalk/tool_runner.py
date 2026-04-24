"""Tool execution helpers for RohTalk.

This module provides the execution seam for RohTalk tool calls.

Current role:
- accept a normalized tool call
- route execution to a configured backend
- return a normalized result payload that the tool loop can always
  append back into conversation history

Design intent:
- local in-process tools remain a valid fallback/bootstrap path
- SkillCLI-backed execution is the intended primary long-term path
- the tool loop should not care how a tool was executed
- this module is the seam that allows execution backends to evolve
  without changing tool loop behavior
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Literal, Mapping, Optional

from Core.LLMClient.types import ToolCall


ToolExecutionMode = Literal["local", "skillcli"]
ToolImplMap = Mapping[str, Callable[..., Any]]
SkillNameMap = Mapping[str, str]
SkillExecutor = Callable[[Any, str, Dict[str, Any]], Any]


def _error_result(
    *,
    tool_name: str,
    tool_call_id: str,
    error: str,
) -> Dict[str, Any]:
    """Build a normalized failed tool result."""
    return {
        "ok": False,
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "error": error,
    }


def _success_result(
    *,
    tool_name: str,
    tool_call_id: str,
    result: Any,
) -> Dict[str, Any]:
    """Build a normalized successful tool result."""
    return {
        "ok": True,
        "tool_name": tool_name,
        "tool_call_id": tool_call_id,
        "result": result,
    }


def _resolve_skill_name(
    tool_name: str,
    skill_name_map: Optional[SkillNameMap],
) -> str:
    """Resolve a tool name to a SkillCLI skill name."""
    if skill_name_map is None:
        return tool_name

    mapped = skill_name_map.get(tool_name)
    if mapped is None or str(mapped).strip() == "":
        return tool_name

    return str(mapped).strip()


def _execute_local_tool(
    *,
    tool_name: str,
    tool_call_id: str,
    arguments: Dict[str, Any],
    tool_impl: Optional[ToolImplMap],
) -> Dict[str, Any]:
    """Execute a tool via direct in-process callables."""
    if tool_name == "":
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error="Tool call is missing a tool name.",
        )

    if tool_impl is None:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=f"No local tool implementation map was provided for tool: {tool_name}",
        )

    fn = tool_impl.get(tool_name)
    if fn is None:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=f"Unknown tool: {tool_name}",
        )

    try:
        result = fn(**arguments)
    except Exception as exc:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=str(exc),
        )

    return _success_result(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        result=result,
    )


def _execute_skillcli_tool(
    *,
    tool_name: str,
    tool_call_id: str,
    arguments: Dict[str, Any],
    ctx: Any,
    skill_name_map: Optional[SkillNameMap],
    skill_executor: Optional[SkillExecutor],
) -> Dict[str, Any]:
    """Execute a tool through a SkillCLI-backed executor seam."""
    if tool_name == "":
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error="Tool call is missing a tool name.",
        )

    if ctx is None:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=f"SkillCLI execution requires ctx for tool: {tool_name}",
        )

    if skill_executor is None:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=f"No SkillCLI executor was provided for tool: {tool_name}",
        )

    skill_name = _resolve_skill_name(tool_name, skill_name_map)

    try:
        result = skill_executor(ctx, skill_name, arguments)
    except Exception as exc:
        return _error_result(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            error=str(exc),
        )

    return _success_result(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        result=result,
    )


def execute_tool_call(
    tool_call: ToolCall,
    tool_impl: Optional[ToolImplMap] = None,
    *,
    execution_mode: ToolExecutionMode = "local",
    ctx: Any = None,
    skill_name_map: Optional[SkillNameMap] = None,
    skill_executor: Optional[SkillExecutor] = None,
) -> Dict[str, Any]:
    """Execute a normalized tool call and return a normalized result payload.

    This function is intentionally backward compatible with the original
    local-callable implementation.

    Local mode:
    - uses in-process Python callables from ``tool_impl``

    SkillCLI mode:
    - resolves the tool name to a SkillCLI skill name
    - delegates execution to ``skill_executor``

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
    arguments = dict(tool_call.arguments or {})

    if execution_mode == "local":
        return _execute_local_tool(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            arguments=arguments,
            tool_impl=tool_impl,
        )

    if execution_mode == "skillcli":
        return _execute_skillcli_tool(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            arguments=arguments,
            ctx=ctx,
            skill_name_map=skill_name_map,
            skill_executor=skill_executor,
        )

    return _error_result(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        error=f"Unsupported tool execution mode: {execution_mode}",
    )
