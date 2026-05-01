"""AutoRoh prompt construction helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from Core.AutoRoh.policy import build_action_cooldown_block


DEFAULT_LOOP_PROMPT = (
    "AutoRoh tick.\n"
    "You are running inside a supervised automation loop.\n"
    "Use tools for live/external truth such as game state, time, weather, or files.\n"
    "Do not guess live data or reuse old tool results as current truth.\n"
    "Handle new human notes or new observed state.\n"
    "If you need to affect the game or external systems, use tools.\n"
    "If nothing meaningful changed, reply exactly: wait\n"
)


def build_tick_prompt(
    base_prompt: str,
    state: Dict[str, Any],
    latest_note: Optional[str],
) -> str:
    last_action = str(state.get("last_action_signature") or "none")
    last_processed = int(state.get("last_processed_message_index", 0) or 0)
    last_note_index = int(state.get("last_human_note_index", -1))
    note_block = latest_note if latest_note else "(no new human note)"
    cooldown_block = build_action_cooldown_block(state)

    return (
        f"{base_prompt}\n\n"
        "State:\n"
        f"- last_action: {last_action}\n"
        f"- last_message_index: {last_processed}\n"
        f"- last_note_index: {last_note_index}\n"
        f"- new_note: {note_block}\n\n"
        "Action cooldowns:\n"
        f"{cooldown_block}\n\n"
        "Behavior:\n"
        "- If nothing meaningful changed, reply exactly: wait\n"
        "- If you want to say something only to the terminal, reply with a short message\n"
        "- If you want to affect the game or external world, call an available tool\n"
        "- If the user asks you to announce something in game, call command_write with type announce_text\n"
        "- If the user asks for an objective or recovery task, call command_write with type set_objective_collect_item\n\n"
        "Rules:\n"
        "- Do not repeat the last action unless new state or a new human note exists\n"
        "- Respect action cooldowns unless there is a human note or critical state change\n"
        "- Prefer provided observations and tool results over assumptions\n"
        "- Never use XML-style tags like <act_now>, <comment>, <tool_action>, or <wait>\n"
        "- Do not describe a game action in text when command_write can perform it\n"
        "- Keep terminal-only replies short\n"
    )
