"""Generic AutoRoh director pack helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class DirectorPack:
    name: str
    domain: str
    style_lines: tuple[str, ...]
    anti_spam_lines: tuple[str, ...]
    situation_themes: Mapping[str, tuple[str, ...]]
    announce_examples: tuple[str, ...]
    objective_templates: tuple[str, ...]
    safe_collect_prefabs: tuple[str, ...]
    safe_reward_prefabs: tuple[str, ...]
    reward_count_ranges: Mapping[str, tuple[int, int]]
    constraints: tuple[str, ...]


REQUIRED_DIRECTOR_PACK_KEYS = {
    "name",
    "domain",
    "style_lines",
    "anti_spam_lines",
    "situation_themes",
    "announce_examples",
    "objective_templates",
    "safe_collect_prefabs",
    "safe_reward_prefabs",
    "reward_count_ranges",
    "constraints",
}


def _require_mapping(value: Any, *, key: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Director pack key {key!r} must be an object.")
    return value


def _string_tuple(value: Any, *, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Director pack key {key!r} must be a list of strings.")
    return tuple(str(item) for item in value)


def _theme_map(value: Any, *, key: str) -> Mapping[str, tuple[str, ...]]:
    mapping = _require_mapping(value, key=key)
    return {
        str(theme): _string_tuple(lines, key=f"{key}.{theme}")
        for theme, lines in mapping.items()
    }


def _reward_range_map(value: Any, *, key: str) -> Mapping[str, tuple[int, int]]:
    mapping = _require_mapping(value, key=key)
    ranges: dict[str, tuple[int, int]] = {}

    for prefab, range_value in mapping.items():
        if (
            not isinstance(range_value, list)
            or len(range_value) != 2
            or not all(isinstance(item, int) for item in range_value)
        ):
            raise ValueError(
                f"Director pack key {key}.{prefab!s} must be a two-integer list."
            )

        minimum, maximum = int(range_value[0]), int(range_value[1])
        if minimum < 1 or maximum < minimum:
            raise ValueError(
                f"Director pack key {key}.{prefab!s} must have a valid positive range."
            )

        ranges[str(prefab)] = (minimum, maximum)

    return ranges


def load_director_pack(path: str | Path) -> DirectorPack:
    pack_path = Path(path)
    raw = json.loads(pack_path.read_text(encoding="utf-8"))
    data = _require_mapping(raw, key=str(pack_path))

    missing = sorted(REQUIRED_DIRECTOR_PACK_KEYS.difference(data))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Director pack {pack_path} missing required keys: {missing_text}")

    name = data["name"]
    domain = data["domain"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Director pack key 'name' must be a non-empty string.")
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("Director pack key 'domain' must be a non-empty string.")

    return DirectorPack(
        name=name,
        domain=domain,
        style_lines=_string_tuple(data["style_lines"], key="style_lines"),
        anti_spam_lines=_string_tuple(data["anti_spam_lines"], key="anti_spam_lines"),
        situation_themes=_theme_map(data["situation_themes"], key="situation_themes"),
        announce_examples=_string_tuple(data["announce_examples"], key="announce_examples"),
        objective_templates=_string_tuple(
            data["objective_templates"],
            key="objective_templates",
        ),
        safe_collect_prefabs=_string_tuple(
            data["safe_collect_prefabs"],
            key="safe_collect_prefabs",
        ),
        safe_reward_prefabs=_string_tuple(
            data["safe_reward_prefabs"],
            key="safe_reward_prefabs",
        ),
        reward_count_ranges=_reward_range_map(
            data["reward_count_ranges"],
            key="reward_count_ranges",
        ),
        constraints=_string_tuple(data["constraints"], key="constraints"),
    )


def _bullet_lines(lines: tuple[str, ...]) -> list[str]:
    return [f"- {line}" for line in lines]


def render_director_pack_prompt(pack: DirectorPack) -> str:
    """Render compact domain guidance for inclusion in every AutoRoh tick."""
    rendered: list[str] = [
        f"Pack: {pack.name} ({pack.domain})",
        "Style:",
        *_bullet_lines(pack.style_lines),
        "Anti-spam:",
        *_bullet_lines(pack.anti_spam_lines),
    ]

    if pack.situation_themes:
        theme_parts = []
        for theme, lines in pack.situation_themes.items():
            theme_parts.append(f"{theme}: {'; '.join(lines)}")
        rendered.append("Themes:")
        rendered.extend(_bullet_lines(tuple(theme_parts)))

    rendered.extend(
        [
            "Announce examples:",
            *_bullet_lines(pack.announce_examples),
            "Objective templates:",
            *_bullet_lines(pack.objective_templates),
            "Safe collect prefabs:",
            f"- {', '.join(pack.safe_collect_prefabs)}",
            "Safe reward prefabs:",
            f"- {', '.join(pack.safe_reward_prefabs)}",
        ]
    )

    if pack.reward_count_ranges:
        ranges = [
            f"{prefab} {minimum}-{maximum}"
            for prefab, (minimum, maximum) in pack.reward_count_ranges.items()
        ]
        rendered.append("Reward count ranges:")
        rendered.append(f"- {', '.join(ranges)}")

    rendered.extend(
        [
            "Constraints:",
            *_bullet_lines(pack.constraints),
        ]
    )

    return "\n".join(rendered)
