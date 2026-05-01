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
from typing import Any, Dict, List, Optional, Sequence

from Core.AutoRoh.profiles import ActionCooldown


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
    cooldowns: Sequence[ActionCooldown] = (),
) -> str:
    """Build an advisory cooldown block for the AutoRoh tick prompt.

    This is profile supplied policy. Cooldowns are advisory only; tools are
    not hard-blocked here.
    """
    if not cooldowns:
        return "- none"

    last_action = str(state.get("last_action_signature") or "")
    last_action_at = state.get("last_action_at")
    elapsed = seconds_since(last_action_at)

    lines: List[str] = []

    for cooldown in cooldowns:
        if (
            last_action == cooldown.signature
            and elapsed is not None
            and elapsed < cooldown.seconds
        ):
            remaining = int(round(cooldown.seconds - elapsed))
            elapsed_int = int(round(elapsed))
            lines.append(
                f"- {cooldown.label}: cooling down, last used {elapsed_int}s ago, "
                f"wait about {remaining}s unless a human note or critical event requires it"
            )
        else:
            lines.append(f"- {cooldown.label}: available")

    return "\n".join(lines)
