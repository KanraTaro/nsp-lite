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

from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import ToolDef

from .tool_runner import ToolImplMap, execute_tool_call


StepCallback = Callable[[int], None]
TextDeltaCallback = Callable[[str], None]
AssistantCallback = Callable[[Dict[str, Any]], None]
ToolCallCallback = Callable[[Any], None]
ToolResultCallback = Callable[[Dict[str, Any]], None]


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
    tool_impl: ToolImplMap,
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
    """Run a tool-capable conversation loop and return final text plus history.

    Parameters:
        messages: Existing normalized conversation history to continue from.
        model: Model name for the LLM backend.
        tools: Tool definitions exposed to the model.
        tool_impl: Mapping of tool name to callable implementation.
        host: Optional backend host override.
        timeout_s: Optional timeout passed to the backend.
        max_steps: Maximum number of assistant turns before aborting.
        client: Optional injected ``LLMClient`` for tests or custom backends.
        on_step: Optional callback fired at the beginning of each loop step.
        on_text_delta: Optional callback fired for each streamed text delta.
        on_assistant_message: Optional callback fired after the assistant
            message is appended to history.
        on_tool_call: Optional callback fired before each tool execution.
        on_tool_result: Optional callback fired after each tool result is produced.

    Returns:
        A tuple ``(final_text, final_messages)`` where:
        - ``final_text`` is the assistant's last text response
        - ``final_messages`` is the fully updated normalized history

    Raises:
        RuntimeError: if the loop exceeds ``max_steps`` without resolving.
        LLMClientError subclasses: propagated from the underlying client.
    """
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

        if not result.tool_calls:
            return result.text, active_messages

        for tool_call in result.tool_calls:
            if on_tool_call is not None:
                on_tool_call(tool_call)

            tool_result = execute_tool_call(tool_call, tool_impl)

            if on_tool_result is not None:
                on_tool_result(tool_result)

            active_messages.append(_build_tool_result_message(tool_result))

    raise RuntimeError(f"Hit max_steps={max_steps} without resolving tool calls.")
