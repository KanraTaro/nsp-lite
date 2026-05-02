"""AutoRoh profile definitions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Core.AutoRoh.director_packs import DirectorPack, load_director_pack


@dataclass(frozen=True)
class ActionCooldown:
    signature: str
    label: str
    seconds: int


@dataclass(frozen=True)
class AutoRohProfile:
    name: str
    behavior_lines: tuple[str, ...] = ()
    rule_lines: tuple[str, ...] = ()
    cooldowns: tuple[ActionCooldown, ...] = ()
    director_pack: DirectorPack | None = None


DST_DIRECTOR_PACK_PATH = (
    Path(__file__).resolve().parents[1]
    / "Game"
    / "DST"
    / "DirectorPacks"
    / "dst_director_v0.json"
)
DST_DIRECTOR_PACK = load_director_pack(DST_DIRECTOR_PACK_PATH)


BASIC_PROFILE = AutoRohProfile(name="basic")

DST_DIRECTOR_PROFILE = AutoRohProfile(
    name="dst_director",
    behavior_lines=(
        "- If the user asks you to announce something in game, call announce_text",
        "- If the user asks for a line, atmospheric line, warning, announcement, message, or tell players request, call announce_text",
        "- If the user asks for an objective or recovery task, call objective_collect",
        "- If the user asks you to remove the current objective, call objective_clear",
    ),
    rule_lines=(
        "- Do not describe a game action in text when a DST tool can perform it",
        "- Use terminal-only replies for status, explanation, or analysis, not player-facing in-game lines",
        "- Use at most one DST action/tool action per tick unless a human explicitly asks for multiple",
    ),
    cooldowns=(
        ActionCooldown(
            signature="tool:announce_text",
            label="announce_text",
            seconds=60,
        ),
        ActionCooldown(
            signature="tool:objective_collect",
            label="objective_collect",
            seconds=180,
        ),
        ActionCooldown(
            signature="tool:objective_clear",
            label="objective_clear",
            seconds=30,
        ),
    ),
    director_pack=DST_DIRECTOR_PACK,
)


def resolve_autoroh_profile(name_or_toolkit: str | None) -> AutoRohProfile:
    name = str(name_or_toolkit or "").strip().lower()

    if name in {"", "basic"}:
        return BASIC_PROFILE

    if name in {"dst", "dst_director", "game_dst"}:
        return DST_DIRECTOR_PROFILE

    return BASIC_PROFILE
