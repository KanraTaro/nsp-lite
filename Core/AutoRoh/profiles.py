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
class NoteRoutingHint:
    match_terms: tuple[str, ...]
    expected_tool: str
    player_facing_request: bool = False
    instruction: str = ""


@dataclass(frozen=True)
class AutoRohProfile:
    name: str
    behavior_lines: tuple[str, ...] = ()
    rule_lines: tuple[str, ...] = ()
    cooldowns: tuple[ActionCooldown, ...] = ()
    director_pack: DirectorPack | None = None
    note_routing_hints: tuple[NoteRoutingHint, ...] = ()
    action_tool_names: tuple[str, ...] = ()
    max_successful_action_tools_per_tick: int | None = None


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
    action_tool_names=(
        "announce_text",
        "objective_collect",
        "objective_clear",
        "chaos_set_tier",
        "supplies_spawn",
        "enemy_spawn",
        "event_trigger",
        "spawned_enemies_clear",
        "spawned_bosses_clear",
        "player_objective_collect",
        "player_objective_clear",
    ),
    max_successful_action_tools_per_tick=1,
    behavior_lines=(
        "- If the user asks you to announce something in game, call announce_text",
        "- If the user asks for an announcement, message to players, tell players request, atmospheric announcement, or warning to players, call announce_text",
        "- If the user asks for an objective or recovery task, call objective_collect",
        "- If the user asks for a per-player objective, call player_objective_collect",
        "- If the user asks you to remove the current objective, call objective_clear",
        "- Use supplies_spawn, enemy_spawn, event_trigger, and cleanup tools only for explicit direction or strong game-state pacing reasons",
    ),
    rule_lines=(
        "- Do not describe a game action in text when a DST tool can perform it",
        "- Use terminal-only replies for status, explanation, or analysis, not player-facing in-game lines",
        "- Use at most one DST action/tool action per tick unless a human explicitly asks for multiple",
        "- Spawn deerclops only after setting chaos tier 3, and use force_boss=true explicitly",
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
        ActionCooldown(
            signature="tool:chaos_set_tier",
            label="chaos_set_tier",
            seconds=120,
        ),
        ActionCooldown(
            signature="tool:supplies_spawn",
            label="supplies_spawn",
            seconds=120,
        ),
        ActionCooldown(
            signature="tool:enemy_spawn",
            label="enemy_spawn",
            seconds=180,
        ),
        ActionCooldown(
            signature="tool:event_trigger",
            label="event_trigger",
            seconds=240,
        ),
        ActionCooldown(
            signature="tool:spawned_enemies_clear",
            label="spawned_enemies_clear",
            seconds=30,
        ),
        ActionCooldown(
            signature="tool:spawned_bosses_clear",
            label="spawned_bosses_clear",
            seconds=30,
        ),
        ActionCooldown(
            signature="tool:player_objective_collect",
            label="player_objective_collect",
            seconds=180,
        ),
        ActionCooldown(
            signature="tool:player_objective_clear",
            label="player_objective_clear",
            seconds=30,
        ),
    ),
    director_pack=DST_DIRECTOR_PACK,
    note_routing_hints=(
        NoteRoutingHint(
            match_terms=(
                "announce",
                "announcement",
                "announce to players",
                "player announcement",
                "in-game announcement",
                "message to players",
                "tell players",
                "atmospheric announcement",
                "warning to players",
            ),
            expected_tool="announce_text",
            player_facing_request=True,
            instruction="do not satisfy this note with terminal-only text",
        ),
    ),
)


def resolve_autoroh_profile(name_or_toolkit: str | None) -> AutoRohProfile:
    name = str(name_or_toolkit or "").strip().lower()

    if name in {"", "basic"}:
        return BASIC_PROFILE

    if name in {"dst", "dst_director", "game_dst"}:
        return DST_DIRECTOR_PROFILE

    return BASIC_PROFILE
