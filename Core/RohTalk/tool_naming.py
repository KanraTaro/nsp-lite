"""Tool naming helpers for RohTalk.

These helpers separate:

- canonical skill identity
- model-facing tool identity

Design intent:
- keep SkillCLI canonical names as the source of truth
- expose model-friendly tool names automatically
- avoid manual per-tool alias registration for normal cases
- use namespace fallback only when collisions occur
"""

from __future__ import annotations

from typing import Dict, List


_VERB_FIRST_ACTIONS = {
    "get",
    "set",
    "create",
    "delete",
    "update",
    "fetch",
    "list",
    "find",
}


def _clean_parts(skill_name: str) -> List[str]:
    cleaned = str(skill_name).strip()
    if cleaned == "":
        raise ValueError("Skill name cannot be empty.")

    parts = [part.strip() for part in cleaned.split(".") if str(part).strip() != ""]
    if len(parts) == 0:
        raise ValueError("Skill name cannot be empty.")

    return parts


def skill_name_to_tool_name(skill_name: str) -> str:
    """Convert a canonical skill name into a model-friendly tool name.

    Preferred behavior:
    - preserve semantic meaning
    - omit generic namespace segments when possible
    - generate clean function-like names by default

    Examples:
        NSPL.Tools.Weather.get -> get_weather
        NSPL.Tools.Time.now -> time_now
        RohTalk.chat -> rohtalk_chat
    """
    parts = _clean_parts(skill_name)

    if len(parts) > 1 and parts[0].lower() == "nspl":
        parts = parts[1:]

    if len(parts) > 1 and parts[0].lower() == "tools":
        parts = parts[1:]

    lowered = [part.lower() for part in parts]

    if len(lowered) >= 2:
        domain = lowered[-2]
        action = lowered[-1]

        if action in _VERB_FIRST_ACTIONS:
            return f"{action}_{domain}"

        return f"{domain}_{action}"

    return "_".join(lowered)


def build_skill_tool_name_map(skill_names: List[str]) -> Dict[str, str]:
    """Build model-facing tool name -> canonical skill name map.

    First pass:
    - generate semantic preferred names

    Second pass:
    - detect collisions
    - fall back to namespaced aliases only for colliding entries

    Example:
        NSPL.Tools.Weather.get -> get_weather
        Game.Tools.Weather.get -> game_get_weather
        NSPL.Tools.Weather.get -> nspl_get_weather (if collision exists)
    """
    preferred_to_skills: Dict[str, List[str]] = {}

    for skill_name in skill_names:
        preferred = skill_name_to_tool_name(skill_name)
        preferred_to_skills.setdefault(preferred, []).append(skill_name)

    result: Dict[str, str] = {}

    for preferred_name, skills in preferred_to_skills.items():
        if len(skills) == 1:
            result[preferred_name] = skills[0]
            continue

        for skill_name in skills:
            parts = _clean_parts(skill_name)
            namespace = parts[0].lower()
            namespaced_name = f"{namespace}_{preferred_name}"

            if namespaced_name in result and result[namespaced_name] != skill_name:
                raise ValueError(
                    f"Tool naming collision could not be resolved automatically: "
                    f"{skill_name} -> {namespaced_name}"
                )

            result[namespaced_name] = skill_name

    return result
