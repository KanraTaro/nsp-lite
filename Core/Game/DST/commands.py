"""DST command contract facts and validation helpers."""

from __future__ import annotations


CANONICAL_COMMAND_TYPES = (
    "announce_text",
    "grant_reward_item",
    "set_objective",
    "set_objective_collect_item",
    "clear_objective",
)

MODEL_SAFE_COMMAND_TYPES = (
    "announce_text",
    "set_objective_collect_item",
    "clear_objective",
)

COMMAND_TYPE_ALIASES = {
    "announce": "announce_text",
}

ACCEPTED_COMMAND_TYPES = tuple(
    sorted(set(CANONICAL_COMMAND_TYPES).union(COMMAND_TYPE_ALIASES))
)


def normalize_command_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return COMMAND_TYPE_ALIASES.get(normalized, normalized)


def validate_command_type(value: str) -> str:
    command_type = normalize_command_type(value)

    if command_type in CANONICAL_COMMAND_TYPES:
        return command_type

    supported = ", ".join(CANONICAL_COMMAND_TYPES)
    raise ValueError(
        f"Unsupported DST command type {value!r}. "
        f"Supported canonical types: {supported}."
    )
