"""AutoRoh policy helpers.

This module owns small reusable policy decisions for AutoRoh loops.

Current scope:
- build advisory action cooldown text for model prompts
- keep policy logic out of Skills/AutoRoh/run/skill.py
- provide a future home for toolkit-specific or director-pack policy

This is intentionally advisory for now. The model sees cooldown state,
but tools are not hard-blocked here yet.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional


DEFAULT_COMMAND_COOLDOWNS_SEC: Dict[str, int] = {
    "announce_text": 60,
    "set_objective_collect_item": 180,
    "clear_objective": 30,
}


def parse_utc_iso(value: Any) -> Optional[datetime]:
    """Parse an ISO-ish UTC timestamp.

    Supports timestamps ending in Z, plus normal offset-aware ISO strings.
    Naive timestamps are treated as UTC.
    """
    text = str(value or "").strip()
    if text == "":
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except Exception:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def seconds_since(value: Any) -> Optional[float]:
    """Return seconds since a timestamp, or None when unavailable."""
    parsed = parse_utc_iso(value)
    if parsed is None:
        return None

    return max(0.0, (datetime.now(UTC) - parsed).total_seconds())


def build_action_cooldown_block(
    state: Dict[str, Any],
    *,
    cooldowns_sec: Optional[Dict[str, int]] = None,
) -> str:
    """Build an advisory cooldown block for the AutoRoh tick prompt.

    The current implementation understands command_write action signatures:

        tool:command_write:announce_text
        tool:command_write:set_objective_collect_item
        tool:command_write:clear_objective

    Later this can be expanded to toolkit/director-pack supplied policy.
    """
    cooldowns = cooldowns_sec or DEFAULT_COMMAND_COOLDOWNS_SEC

    last_action = str(state.get("last_action_signature") or "")
    last_action_at = state.get("last_action_at")
    elapsed = seconds_since(last_action_at)

    lines: List[str] = []

    for command_type, cooldown_sec in cooldowns.items():
        action_key = f"tool:command_write:{command_type}"

        if last_action == action_key and elapsed is not None and elapsed < cooldown_sec:
            remaining = int(round(cooldown_sec - elapsed))
            elapsed_int = int(round(elapsed))
            lines.append(
                f"- {command_type}: cooling down, last used {elapsed_int}s ago, "
                f"wait about {remaining}s unless a human note or critical event requires it"
            )
        else:
            lines.append(f"- {command_type}: available")

    return "\n".join(lines)
