"""Tool-capable conversation loop for RohTalk.

This module provides a minimal backend-agnostic tool loop built on top
of LLMClient's normalized chat contract.

Current role:
- run a streamed model turn via ``chat_stream_collect(...)``
- append the normalized assistant message to history
- execute any requested tools through ``tool_runner``
- append normalized tool result messages
- repeat until the model returns a final non-tool response or the loop
  hits the configured maximum number of steps

Design constraints:
- prefer streaming whenever the backend supports it
- do not encode provider-specific message schemas here
- do not assume tools always succeed
- do not assume tool execution always uses direct Python callables
- keep execution delegated to ``tool_runner`` so the backend can later
  be swapped to SkillCLI-backed execution without changing loop logic
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import ToolDef

from .tool_runner import (
    SkillExecutor,
    SkillNameMap,
    ToolExecutionMode,
    ToolImplMap,
    execute_tool_call,
)


StepCallback = Callable[[int], None]
TextDeltaCallback = Callable[[str], None]
AssistantCallback = Callable[[Dict[str, Any]], None]
ToolCallCallback = Callable[[Any], None]
ToolResultCallback = Callable[[Dict[str, Any]], None]

@dataclass(frozen=True)
class CompatToolCall:
    """Tool call recovered from model text when the backend did not emit a real tool call."""

    id: str
    name: str
    arguments: Dict[str, Any]


def _tool_names(tools: List[ToolDef]) -> set[str]:
    names: set[str] = set()
    for tool in tools:
        name = str(getattr(tool, "name", "") or "").strip()
        if name:
            names.add(name)
    return names


def _try_parse_text_tool_call(text: str, tools: List[ToolDef]) -> Optional[CompatToolCall]:
    """Recover a strict JSON tool call emitted as assistant text.

    This intentionally supports only a narrow compatibility shape:
    {"name": "...", "arguments": {...}}

    Do not expand this into broad natural-language command parsing.
    """
    clean_text = str(text or "").strip()
    if not clean_text.startswith("{") or not clean_text.endswith("}"):
        return None

    try:
        payload = json.loads(clean_text)
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    raw_name = payload.get("name", payload.get("tool_name"))
    name = str(raw_name or "").strip()
    if name == "":
        return None

    if name not in _tool_names(tools):
        return None

    arguments = payload.get("arguments", {})
    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return None

    return CompatToolCall(
        id=str(payload.get("id", "compat_call_0") or "compat_call_0"),
        name=name,
        arguments=arguments,
    )

def _build_tool_result_message(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a normalized tool execution result into a history message."""
    return {
        "role": "tool",
        "tool_call_id": str(tool_result.get("tool_call_id", "") or ""),
        "tool_name": str(tool_result.get("tool_name", "") or ""),
        "content": json.dumps(tool_result, separators=(",", ":"), sort_keys=True),
    }


def run_tool_loop(
    messages: List[Dict[str, Any]],
    *,
    model: str,
    tools: List[ToolDef],
    tool_impl: Optional[ToolImplMap] = None,
    execution_mode: ToolExecutionMode = "local",
    ctx: Any = None,
    skill_name_map: Optional[SkillNameMap] = None,
    skill_executor: Optional[SkillExecutor] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    max_steps: int = 5,
    client: Optional[LLMClient] = None,
    on_step: Optional[StepCallback] = None,
    on_text_delta: Optional[TextDeltaCallback] = None,
    on_assistant_message: Optional[AssistantCallback] = None,
    on_tool_call: Optional[ToolCallCallback] = None,
    on_tool_result: Optional[ToolResultCallback] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Run a tool-capable conversation loop and return final text plus history."""
    active_messages: List[Dict[str, Any]] = list(messages)
    active_client = client or LLMClient()

    for step_index in range(max_steps):
        if on_step is not None:
            on_step(step_index)

        result = active_client.chat_stream_collect(
            active_messages,
            model=model,
            host=host,
            timeout_s=timeout_s,
            tools=tools,
            on_text_delta=on_text_delta,
        )

        active_messages.append(result.assistant_message)

        if on_assistant_message is not None:
            on_assistant_message(result.assistant_message)

        tool_calls = list(result.tool_calls)

        if not tool_calls:
            compat_tool_call = _try_parse_text_tool_call(result.text, tools)
            if compat_tool_call is None:
                return result.text, active_messages

            tool_calls = [compat_tool_call]

        for tool_call in tool_calls:
            if on_tool_call is not None:
                on_tool_call(tool_call)

            tool_result = execute_tool_call(
                tool_call,
                tool_impl,
                execution_mode=execution_mode,
                ctx=ctx,
                skill_name_map=skill_name_map,
                skill_executor=skill_executor,
            )

            if on_tool_result is not None:
                on_tool_result(tool_result)

            active_messages.append(_build_tool_result_message(tool_result))

    raise RuntimeError(f"Hit max_steps={max_steps} without resolving tool calls.")
