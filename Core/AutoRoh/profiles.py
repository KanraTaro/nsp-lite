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
        "- If the user asks you to announce something in game, call command_write with type announce_text",
        "- If the user asks for an objective or recovery task, call command_write with type set_objective_collect_item",
    ),
    rule_lines=(
        "- Do not describe a game action in text when command_write can perform it",
        "- Use at most one command_write action per tick unless a human explicitly asks for multiple",
    ),
    cooldowns=(
        ActionCooldown(
            signature="tool:command_write:announce_text",
            label="announce_text",
            seconds=60,
        ),
        ActionCooldown(
            signature="tool:command_write:set_objective_collect_item",
            label="set_objective_collect_item",
            seconds=180,
        ),
        ActionCooldown(
            signature="tool:command_write:clear_objective",
            label="clear_objective",
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
