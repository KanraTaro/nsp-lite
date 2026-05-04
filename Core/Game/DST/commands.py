"""DST command contract facts and validation helpers."""

from __future__ import annotations

from typing import Any, Dict


CANONICAL_COMMAND_TYPES = (
    "announce_text",
    "grant_reward_item",
    "set_objective",
    "set_objective_collect_item",
    "set_player_objective_collect_item",
    "clear_objective",
    "clear_player_objective",
    "objective_status",
    "set_chaos_tier",
    "spawn_supplies",
    "spawn_enemy",
    "trigger_event",
    "clear_spawned_enemies",
    "clear_spawned_bosses",
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

TARGET_MODES = (
    "first",
    "random",
    "lowest_hunger",
    "lowest_sanity",
    "lowest_health",
    "ghost",
    "alive",
)

SAFE_SUPPLY_PREFABS = (
    "cutgrass",
    "twigs",
    "flint",
    "log",
    "rocks",
    "berries",
    "carrot",
    "torch",
    "rope",
    "boards",
    "goldnugget",
    "healingsalve",
    "spidergland",
    "silk",
    "charcoal",
    "honey",
    "meat",
    "gears",
    "marble",
    "nightmarefuel",
    "livinglog",
)

SAFE_ENEMY_PREFABS = (
    "spider",
    "frog",
    "bee",
    "killerbee",
    "spider_warrior",
    "hound",
    "bat",
    "firehound",
    "icehound",
    "tentacle",
    "tallbird",
    "deerclops",
)

SAFE_BOSS_PREFABS = ("deerclops",)

SAFE_EVENT_NAMES = (
    "frog_rain_light",
    "frog_rain_medium",
)

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


def clean_text(value: str) -> str:
    return str(value or "").strip()


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


def validate_target_mode(value: str) -> str:
    target_mode = str(value or "").strip().lower()

    if target_mode in TARGET_MODES:
        return target_mode

    supported = ", ".join(TARGET_MODES)
    raise ValueError(
        f"Unsupported DST target_mode {value!r}. "
        f"Supported target modes: {supported}."
    )


def validate_supply_prefab(value: str) -> str:
    prefab = normalize_prefab(value)

    if prefab in SAFE_SUPPLY_PREFABS:
        return prefab

    supported = ", ".join(SAFE_SUPPLY_PREFABS)
    raise ValueError(
        f"Unsupported DST supply prefab {value!r}. "
        f"Safe supply prefabs: {supported}."
    )


def validate_enemy_prefab(value: str) -> str:
    prefab = normalize_prefab(value)

    if prefab in SAFE_ENEMY_PREFABS:
        return prefab

    supported = ", ".join(SAFE_ENEMY_PREFABS)
    raise ValueError(
        f"Unsupported DST enemy prefab {value!r}. "
        f"Safe enemy prefabs: {supported}."
    )


def validate_event_name(value: str) -> str:
    event_name = str(value or "").strip().lower()

    if event_name in SAFE_EVENT_NAMES:
        return event_name

    supported = ", ".join(SAFE_EVENT_NAMES)
    raise ValueError(
        f"Unsupported DST event_name {value!r}. "
        f"Supported event names: {supported}."
    )


def clamp_int_range(
    value: int,
    *,
    default: int,
    min_value: int,
    max_value: int,
) -> int:
    try:
        number = int(value)
    except Exception:
        number = default

    if number < min_value:
        number = min_value

    if number > max_value:
        number = max_value

    return number


def clamp_chaos_tier(value: int) -> int:
    return clamp_int_range(value, default=1, min_value=0, max_value=3)


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


def build_announce_text_command(text: str) -> Dict[str, Any]:
    validate_command_type("announce_text")
    cleaned_text = clean_text(text)

    if cleaned_text == "":
        raise ValueError("announce_text requires text.")

    return {
        "type": "announce_text",
        "payload": {
            "text": cleaned_text,
        },
    }


def build_collect_objective_command(
    title: str,
    text: str,
    target_prefab: str,
    target_count: int,
    reward_prefab: str,
    reward_count: int,
    target_userid: str = "",
) -> Dict[str, Any]:
    validate_command_type("set_objective_collect_item")
    objective_title = clean_text(title) or "Objective"
    objective_text = clean_text(text)
    normalized_target_prefab = validate_collect_prefab(target_prefab)
    normalized_reward_prefab = validate_reward_prefab(reward_prefab or "cutgrass")

    return {
        "type": "set_objective_collect_item",
        "payload": {
            "title": objective_title,
            "text": objective_text,
            "target_userid": clean_text(target_userid),
            "target_prefab": normalized_target_prefab,
            "target_count": clamp_positive_int(target_count),
            "reward_prefab": normalized_reward_prefab,
            "reward_count": clamp_reward_count(normalized_reward_prefab, reward_count),
        },
    }


def build_clear_objective_command() -> Dict[str, Any]:
    validate_command_type("clear_objective")

    return {
        "type": "clear_objective",
        "payload": {},
    }


def build_set_chaos_tier_command(
    chaos_tier: int,
    announce: str = "",
) -> Dict[str, Any]:
    return {
        "type": "set_chaos_tier",
        "chaos_tier": clamp_chaos_tier(chaos_tier),
        "announce": clean_text(announce),
    }


def build_spawn_supplies_command(
    prefab: str,
    count: int = 1,
    target_mode: str = "first",
    radius: int = 4,
    announce: str = "",
) -> Dict[str, Any]:
    return {
        "type": "spawn_supplies",
        "prefab": validate_supply_prefab(prefab),
        "count": clamp_positive_int(count, max_value=20),
        "target_mode": validate_target_mode(target_mode or "first"),
        "radius": clamp_int_range(radius, default=4, min_value=1, max_value=20),
        "announce": clean_text(announce),
    }


def build_spawn_enemy_command(
    prefab: str,
    count: int = 1,
    target_mode: str = "first",
    radius: int = 8,
    announce: str = "",
    force_boss: bool = False,
) -> Dict[str, Any]:
    enemy_prefab = validate_enemy_prefab(prefab)
    payload: Dict[str, Any] = {
        "type": "spawn_enemy",
        "prefab": enemy_prefab,
        "count": clamp_positive_int(count, max_value=10),
        "target_mode": validate_target_mode(target_mode or "first"),
        "radius": clamp_int_range(radius, default=8, min_value=1, max_value=30),
        "announce": clean_text(announce),
    }

    if enemy_prefab in SAFE_BOSS_PREFABS:
        if not bool(force_boss):
            raise ValueError("Boss enemy prefab deerclops requires force_boss=true.")
        payload["force_boss"] = True
        payload["count"] = 1
    elif bool(force_boss):
        raise ValueError("force_boss is only supported for deerclops.")

    return payload


def build_trigger_event_command(
    event_name: str,
    target_mode: str = "first",
    intensity: int = 1,
    duration_seconds: int = 20,
    radius: int = 10,
    announce: str = "",
) -> Dict[str, Any]:
    return {
        "type": "trigger_event",
        "event_name": validate_event_name(event_name),
        "target_mode": validate_target_mode(target_mode or "first"),
        "intensity": clamp_int_range(intensity, default=1, min_value=1, max_value=3),
        "duration_seconds": clamp_int_range(
            duration_seconds,
            default=20,
            min_value=5,
            max_value=120,
        ),
        "radius": clamp_int_range(radius, default=10, min_value=1, max_value=30),
        "announce": clean_text(announce),
    }


def build_clear_spawned_enemies_command(announce: str = "") -> Dict[str, Any]:
    return {
        "type": "clear_spawned_enemies",
        "announce": clean_text(announce),
    }


def build_clear_spawned_bosses_command(announce: str = "") -> Dict[str, Any]:
    return {
        "type": "clear_spawned_bosses",
        "announce": clean_text(announce),
    }


def build_player_collect_objective_command(
    title: str,
    text: str,
    target_prefab: str,
    target_count: int,
    reward_prefab: str,
    reward_count: int,
    target_userid: str = "",
    target_mode: str = "first",
    announce: bool = True,
) -> Dict[str, Any]:
    objective_title = clean_text(title) or "Objective"
    normalized_target_prefab = validate_collect_prefab(target_prefab)
    normalized_reward_prefab = validate_reward_prefab(reward_prefab or "cutgrass")

    return {
        "type": "set_player_objective_collect_item",
        "target_userid": clean_text(target_userid),
        "target_mode": validate_target_mode(target_mode or "first"),
        "title": objective_title,
        "text": clean_text(text),
        "target_prefab": normalized_target_prefab,
        "target_count": clamp_positive_int(target_count),
        "reward_prefab": normalized_reward_prefab,
        "reward_count": clamp_reward_count(normalized_reward_prefab, reward_count),
        "announce": bool(announce),
    }


def build_clear_player_objective_command(
    target_userid: str = "",
    target_mode: str = "first",
    announce: bool = True,
) -> Dict[str, Any]:
    return {
        "type": "clear_player_objective",
        "target_userid": clean_text(target_userid),
        "target_mode": validate_target_mode(target_mode or "first"),
        "announce": bool(announce),
    }


def build_objective_status_command(all: bool = True) -> Dict[str, Any]:
    return {
        "type": "objective_status",
        "all": bool(all),
    }
