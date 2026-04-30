"""AutoRoh.run skill.

Small supervised AutoRoh loop.

This is not full AutoRoh yet. This is the first heartbeat:
- attach to an existing RohTalk conversation or create one
- repeatedly send a loop prompt
- optionally use RohTalk tools/toolkits
- wait between turns
- stop after max turns

Later this grows into observation, policy, compression, tracing, and
game/session state handling.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from Core.AutoRoh.state import (
    load_loop_state,
    mark_idle_skip,
    reset_idle_skip,
    save_loop_state,
    update_after_tick,
    update_observation,
)
from Core.LLMClient.types import LLMClientError
from Core.RohTalk import get_conversation, resolve_conversation_ref, run_turn
from Core.RohTalk.tracing import print_step, print_tool_call, print_tool_result


DEFAULT_LOOP_PROMPT = (
    "AutoRoh tick.\n"
    "You are running inside a supervised automation loop.\n"
    "Use tools for live/external truth such as game state, time, weather, or files.\n"
    "Do not guess live data or reuse old tool results as current truth.\n"
    "Handle new human notes or new observed state.\n"
    "If you need to affect the game or external systems, use tools.\n"
    "If nothing meaningful changed, reply exactly: wait\n"
)


def _get_messages(ctx: Any, conversation_id: str) -> List[Dict[str, Any]]:
    metadata = get_conversation(ctx, conversation_id)
    messages = metadata.get("messages", [])
    if not isinstance(messages, list):
        return []

    clean_messages: List[Dict[str, Any]] = []
    for message in messages:
        if isinstance(message, dict):
            clean_messages.append(message)

    return clean_messages


def _latest_unhandled_note(
    ctx: Any,
    conversation_id: str,
    last_human_note_index: int,
) -> Tuple[Optional[int], Optional[str]]:
    messages = _get_messages(ctx, conversation_id)

    latest_index: Optional[int] = None
    latest_note: Optional[str] = None

    for index, message in enumerate(messages):
        if index <= last_human_note_index:
            continue

        content = str(message.get("content", "") or "").strip()
        if content.startswith("[human note]"):
            latest_index = index
            latest_note = content

    return latest_index, latest_note


def _build_tick_prompt(
    base_prompt: str,
    state: Dict[str, Any],
    latest_note: Optional[str],
) -> str:
    last_action = str(state.get("last_action_signature") or "none")
    last_processed = int(state.get("last_processed_message_index", 0) or 0)
    last_note_index = int(state.get("last_human_note_index", -1))
    note_block = latest_note if latest_note else "(no new human note)"

    return (
        f"{base_prompt}\n\n"
        "State:\n"
        f"- last_action: {last_action}\n"
        f"- last_message_index: {last_processed}\n"
        f"- last_note_index: {last_note_index}\n"
        f"- new_note: {note_block}\n\n"
        "Behavior:\n"
        "- If nothing meaningful changed, reply exactly: wait\n"
        "- If you want to say something only to the terminal, reply with a short message\n"
        "- If you want to affect the game or external world, call an available tool\n"
        "- If the user asks you to announce something in game, call command_write with type announce_text\n"
        "- If the user asks for an objective or recovery task, call command_write with type set_objective_collect_item\n\n"
        "Rules:\n"
        "- Do not repeat the last action unless new state or a new human note exists\n"
        "- Prefer provided observations and tool results over assumptions\n"
        "- Never use XML-style tags like <act_now>, <comment>, <tool_action>, or <wait>\n"
        "- Do not describe a game action in text when command_write can perform it\n"
        "- Keep terminal-only replies short\n"
    )


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _call_observation_tool(
    ctx: Any,
    *,
    toolkit_name: str,
    tool_name: str,
) -> Tuple[Optional[str], Optional[str]]:
    from Core.RohTalk.skillcli_tools import execute_skill
    from Core.RohTalk.toolkits import resolve_toolkit

    clean_tool_name = str(tool_name or "").strip()
    if clean_tool_name == "":
        return None, None

    toolkit = resolve_toolkit(toolkit_name)
    skill_name = toolkit.skill_name_map.get(clean_tool_name)

    if skill_name is None:
        raise ValueError(f"Observation tool not found in toolkit: {clean_tool_name}")

    result = execute_skill(ctx, skill_name, {})

    signature_source = result
    if isinstance(result, dict) and isinstance(result.get("signature_basis"), dict):
        signature_source = result["signature_basis"]

    summary = _stable_json(result)
    signature = _hash_text(_stable_json(signature_source))

    return signature, summary


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--conversation",
        "--conversation-id",
        dest="conversation_ref",
        default=None,
        help="Existing RohTalk conversation id, short id, or numeric index. If omitted, a new conversation is created.",
    )
    parser.add_argument(
        "--prompt",
        dest="prompt",
        default=DEFAULT_LOOP_PROMPT,
        help="Prompt sent on each AutoRoh loop tick.",
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        type=float,
        default=10.0,
        help="Seconds to wait between loop turns.",
    )
    parser.add_argument(
        "--max-turns",
        dest="max_turns",
        type=int,
        default=5,
        help="Maximum loop turns to run.",
    )
    parser.add_argument(
        "--forever",
        dest="forever",
        action="store_true",
        help="Run until interrupted with Ctrl+C. Ignores --max-turns.",
    )
    parser.add_argument(
        "--title",
        dest="title",
        default="AutoRoh Loop",
        help="Optional title when creating a new conversation.",
    )
    parser.add_argument("--model", dest="model", default=None, help="Optional model override.")
    parser.add_argument("--host", dest="host", default=None, help="Optional backend URL override.")
    parser.add_argument("--tools", dest="tools", action="store_true", help="Enable tool-capable turns.")
    parser.add_argument(
        "--tool-backend",
        dest="tool_backend",
        choices=["skillcli", "local"],
        default="skillcli",
        help="Tool execution backend when --tools is enabled.",
    )
    parser.add_argument(
        "--toolkit",
        dest="toolkit",
        default="basic",
        help="Tool kit to expose when --tools is enabled.",
    )
    parser.add_argument(
        "--tool-trace",
        dest="tool_trace",
        action="store_true",
        help="Print model tool calls and tool results during tool-capable turns.",
    )
    parser.add_argument(
        "--idle-skip",
        dest="idle_skip",
        action="store_true",
        help="Skip model calls when no new note and observed state has not changed.",
    )
    parser.add_argument(
        "--observation-tool",
        dest="observation_tool",
        default=None,
        help="Model-facing tool name to call before each tick, e.g. snapshot_read.",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        conversation_id: Optional[str] = (
            resolve_conversation_ref(ctx, args.conversation_ref)
            if args.conversation_ref
            else None
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    max_turns = int(getattr(args, "max_turns", 5) or 5)
    interval = float(getattr(args, "interval", 10.0) or 10.0)
    forever = bool(getattr(args, "forever", False))
    tool_trace = bool(getattr(args, "tool_trace", False))

    if not forever and max_turns <= 0:
        print("max-turns must be greater than 0 unless --forever is used.", file=sys.stderr)
        return 2

    if interval < 0:
        print("interval must be 0 or greater.", file=sys.stderr)
        return 2

    prompt = str(getattr(args, "prompt", DEFAULT_LOOP_PROMPT) or DEFAULT_LOOP_PROMPT).strip()
    if prompt == "":
        print("prompt cannot be empty.", file=sys.stderr)
        return 2

    idle_skip = bool(getattr(args, "idle_skip", False))
    observation_tool = getattr(args, "observation_tool", None)
    observation_tool = str(observation_tool).strip() if observation_tool else None

    print("AutoRoh loop starting.")
    print(f"conversation: {conversation_id or '(new)'}")
    print(f"max_turns: {'forever' if forever else max_turns}")
    print(f"interval: {interval}")
    print(f"tools: {bool(args.tools)}")
    if args.tools:
        print(f"tool_backend: {args.tool_backend}")
        print(f"toolkit: {args.toolkit}")
        print(f"tool_trace: {tool_trace}")
        print(f"idle_skip: {idle_skip}")
        if observation_tool:
            print(f"observation_tool: {observation_tool}")
    print("")

    try:
        turn_index = 0

        while forever or turn_index < max_turns:
            turn_index += 1
            total_label = "∞" if forever else str(max_turns)
            print(f"[AutoRoh turn {turn_index}/{total_label}]")

            latest_note_index: Optional[int] = None
            tick_prompt = prompt
            observation_signature: Optional[str] = None
            observation_summary: Optional[str] = None
            observation_changed = True

            if conversation_id is not None:
                state = load_loop_state(ctx, conversation_id)

                if observation_tool:
                    observation_signature, observation_summary = _call_observation_tool(
                        ctx,
                        toolkit_name=str(args.toolkit),
                        tool_name=observation_tool,
                    )
                    previous_signature = state.get("last_observation_signature")
                    observation_changed = observation_signature != previous_signature

                latest_note_index, latest_note = _latest_unhandled_note(
                    ctx,
                    conversation_id,
                    int(state.get("last_human_note_index", -1)),
                )

                has_new_note = latest_note_index is not None

                if idle_skip and observation_tool and not observation_changed and not has_new_note:
                    mark_idle_skip(state)
                    update_observation(
                        state,
                        observation_signature=observation_signature,
                        observation_summary=observation_summary,
                    )
                    save_loop_state(ctx, state)
                    print(f"conversation_id: {conversation_id}")
                    print("(idle skip: no new note or observation change)")

                    should_continue = forever or turn_index < max_turns
                    if should_continue and interval > 0:
                        time.sleep(interval)
                    continue

                reset_idle_skip(state)
                update_observation(
                    state,
                    observation_signature=observation_signature,
                    observation_summary=observation_summary,
                )
                save_loop_state(ctx, state)

                tick_prompt = _build_tick_prompt(prompt, state, latest_note)

                if observation_summary:
                    tick_prompt += "\nObservation:\n"
                    tick_prompt += observation_summary
                    tick_prompt += "\n"

            conversation_id, reply = run_turn(
                ctx,
                tick_prompt,
                conversation_id=conversation_id,
                kind="conversation",
                model=args.model,
                host=args.host,
                title=args.title,
                use_tools=bool(args.tools),
                tool_backend=str(args.tool_backend),
                toolkit=str(args.toolkit),
                on_step=print_step if args.tools and tool_trace else None,
                on_tool_call=print_tool_call if args.tools and tool_trace else None,
                on_tool_result=print_tool_result if args.tools and tool_trace else None,
            )

            print(f"conversation_id: {conversation_id}")

            if reply:
                print(reply)
            else:
                print("(empty reply)")

            state = load_loop_state(ctx, conversation_id)
            message_count = len(_get_messages(ctx, conversation_id))
            action_signature: Optional[str] = None

            if reply:
                action_signature = str(reply).strip()[:160]

            update_after_tick(
                ctx,
                state,
                message_count=message_count,
                last_note_index=latest_note_index,
                action_signature=action_signature,
            )
            save_loop_state(ctx, state)

            should_continue = forever or turn_index < max_turns
            if should_continue and interval > 0:
                time.sleep(interval)

        print("")
        print("AutoRoh loop finished.")
        return 0

    except KeyboardInterrupt:
        print("")
        print("AutoRoh loop interrupted.")
        if conversation_id:
            print(f"conversation_id: {conversation_id}")
        return 130
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
