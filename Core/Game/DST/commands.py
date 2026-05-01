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

SAFE_COLLECT_PREFABS = (
    "log",
    "cutgrass",
    "twigs",
    "flint",
    "silk",
    "goldnugget",
)

SAFE_REWARD_PREFABS = SAFE_COLLECT_PREFABS

REWARD_COUNT_RANGES = {
    "log": (1, 4),
    "cutgrass": (2, 6),
    "twigs": (2, 6),
    "flint": (1, 4),
    "silk": (1, 2),
    "goldnugget": (1, 2),
}

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


def normalize_prefab(value: str) -> str:
    return str(value or "").strip().lower()


def validate_collect_prefab(value: str) -> str:
    prefab = normalize_prefab(value)

    if prefab in SAFE_COLLECT_PREFABS:
        return prefab

    supported = ", ".join(SAFE_COLLECT_PREFABS)
    raise ValueError(
        f"Unsupported DST collect prefab {value!r}. "
        f"Safe collect prefabs: {supported}."
    )


def validate_reward_prefab(value: str) -> str:
    prefab = normalize_prefab(value)

    if prefab in SAFE_REWARD_PREFABS:
        return prefab

    supported = ", ".join(SAFE_REWARD_PREFABS)
    raise ValueError(
        f"Unsupported DST reward prefab {value!r}. "
        f"Safe reward prefabs: {supported}."
    )


def clamp_positive_int(value: int, *, default: int = 1, max_value: int = 40) -> int:
    try:
        number = int(value)
    except Exception:
        number = default

    if number < 1:
        number = default

    if number > max_value:
        number = max_value

    return number


def clamp_reward_count(prefab: str, value: int) -> int:
    reward_prefab = validate_reward_prefab(prefab)
    minimum, maximum = REWARD_COUNT_RANGES[reward_prefab]

    try:
        number = int(value)
    except Exception:
        number = minimum

    if number < minimum:
        number = minimum

    if number > maximum:
        number = maximum

    return number
