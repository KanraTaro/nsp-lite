"""
Core/AutoRoh/state.py

Loop state tracking for AutoRoh.

This module ensures:
- We do not reprocess the same messages repeatedly
- We track simple cooldowns and last actions
- State is fully persisted via NodeCTX (FPP compliant)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime


# =========================
# 🧱 Internal helpers
# =========================

def _state_path(ctx: Any, conversation_id: str):
    node_ctx = ctx.node_ctx

    return node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        global_scope=ctx.global_scope,
        domain="AutoRoh",
        bucket="Workflow",
        subpath=f"Loops/{conversation_id}"
    ) / "state.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# =========================
# 🧠 Public API
# =========================

def load_loop_state(ctx: Any, conversation_id: str) -> Dict[str, Any]:
    node_ctx = ctx.node_ctx
    path = _state_path(ctx, conversation_id)

    if not path.exists():
        return _default_state(conversation_id)

    try:
        data = node_ctx.read_json(path)
        if not isinstance(data, dict):
            return _default_state(conversation_id)
        return data
    except Exception:
        return _default_state(conversation_id)


def save_loop_state(ctx: Any, state: Dict[str, Any]) -> None:
    node_ctx = ctx.node_ctx

    conversation_id = str(state.get("conversation_id", "")).strip()
    if not conversation_id:
        return

    path = _state_path(ctx, conversation_id)

    state["updated_at"] = _now_iso()

    node_ctx.write_json_atomic(path, state)


def update_after_tick(
    ctx: Any,
    state: Dict[str, Any],
    *,
    message_count: int,
    last_note_index: Optional[int],
    action_signature: Optional[str],
) -> Dict[str, Any]:
    """
    Update state after a completed AutoRoh tick.
    """

    state["last_processed_message_index"] = int(message_count)

    if last_note_index is not None:
        state["last_human_note_index"] = int(last_note_index)

    if action_signature:
        state["last_action_signature"] = str(action_signature)
        state["last_action_at"] = _now_iso()

    return state


# =========================
# 🔁 Cooldowns (simple)
# =========================

def is_on_cooldown(state: Dict[str, Any], key: str, now_ts: float, cooldown_sec: float) -> bool:
    last = state.get("cooldowns", {}).get(key, 0)
    return (now_ts - last) < cooldown_sec


def set_cooldown(state: Dict[str, Any], key: str, now_ts: float) -> None:
    if "cooldowns" not in state:
        state["cooldowns"] = {}
    state["cooldowns"][key] = float(now_ts)


# =========================
# 🧪 Defaults
# =========================

def _default_state(conversation_id: str) -> Dict[str, Any]:
    return {
        "conversation_id": conversation_id,

        "last_processed_message_index": 0,
        "last_human_note_index": -1,

        "last_action_signature": None,
        "last_action_at": None,

        "cooldowns": {},

        "updated_at": _now_iso(),
    }
