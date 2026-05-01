"""Observation helpers for AutoRoh loops."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, Tuple


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def call_observation_tool(
    ctx: Any,
    *,
    toolkit_name: str,
    tool_name: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Execute a model-facing observation tool and return signature plus summary."""
    from Core.RohTalk.skillcli_tools import execute_skill
    from Core.RohTalk.toolkits import resolve_toolkit

    clean_tool_name = str(tool_name or "").strip()
    if clean_tool_name == "":
        return None, None

    toolkit = resolve_toolkit(toolkit_name)
    skill_name = toolkit.skill_name_map.get(clean_tool_name)

    if skill_name is None:
        raise ValueError(f"Observation tool not found in toolkit: {clean_tool_name}")

    result = execute_skill(ctx, skill_name, {})

    signature_source = result
    if isinstance(result, dict) and isinstance(result.get("signature_basis"), dict):
        signature_source = result["signature_basis"]

    summary = _stable_json(result)
    signature = _hash_text(_stable_json(signature_source))

    return signature, summary
