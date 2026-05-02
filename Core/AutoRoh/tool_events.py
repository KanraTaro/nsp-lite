"""AutoRoh tool event recording helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_tool_arguments(tool_call: Any) -> Dict[str, Any]:
    arguments = getattr(tool_call, "arguments", {})
    if isinstance(arguments, dict):
        return dict(arguments)
    return {}


def record_tool_call(tool_call: Any) -> Dict[str, Any]:
    return {
        "type": "tool_call",
        "name": str(getattr(tool_call, "name", "") or ""),
        "arguments": _safe_tool_arguments(tool_call),
    }


def record_tool_result(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "tool_result",
        "name": str(tool_result.get("tool_name", "") or ""),
        "ok": bool(tool_result.get("ok", False)),
        "result": tool_result.get("result"),
    }


def action_signature_from_tool_events(
    tool_events: List[Dict[str, Any]],
    *,
    action_tool_names: tuple[str, ...] = (),
) -> Optional[str]:
    if action_tool_names:
        action_names = set(action_tool_names)
        for event in reversed(tool_events):
            if event.get("type") != "tool_result":
                continue

            name = str(event.get("name", "") or "")
            if bool(event.get("ok", False)) and name in action_names:
                return f"tool:{name}"

        return None

    for event in reversed(tool_events):
        if event.get("type") != "tool_call":
            continue

        name = str(event.get("name", "") or "")
        arguments = event.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}

        if name == "command_write":
            command_type = str(arguments.get("type", "") or "unknown")
            return f"tool:command_write:{command_type}"

        if name:
            return f"tool:{name}"

    return None
