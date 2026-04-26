"""AutoRoh.run skill.

Small supervised AutoRoh loop.

This is not full AutoRoh yet. This is the first heartbeat:
- attach to an existing RohTalk conversation or create one
- repeatedly send a loop prompt
- optionally use RohTalk tools/toolkits
- wait between turns
- stop after max turns

Later this grows into observation, policy, compression, and game/session
state handling.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from Core.AutoRoh.state import load_loop_state, save_loop_state, update_after_tick
from Core.LLMClient.types import LLMClientError
from Core.RohTalk import get_conversation, resolve_conversation_ref, run_turn


DEFAULT_LOOP_PROMPT = (
    "AutoRoh loop tick.\n\n"
    "You must follow these rules:\n"
    "- If the task requires real-world or external data such as time, weather, files, or game state, you MUST use an available tool.\n"
    "- Do not guess, approximate, or reuse stale real-world data when a tool can check it.\n"
    "- If you need real-world or external data, call a tool during this tick. Do not rely on old tool results from previous ticks unless summarizing history.\n"
    "- Pay special attention to recent [human note] messages. Treat them as guidance for this tick.\n"
    "- Decide whether to wait, comment, suggest, or act.\n"
    "- If nothing meaningful changed, say that you will wait.\n"
    "- If you cannot act safely or cannot access the needed tool, say you will wait and explain briefly.\n"
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
        "Loop state:\n"
        f"- Last action: {last_action}\n"
        f"- Last processed message index: {last_processed}\n"
        f"- Last handled human note index: {last_note_index}\n\n"
        "New human note:\n"
        f"{note_block}\n\n"
        "When handling a human note, choose one:\n"
        "- act_now: act on it this tick\n"
        "- remember: acknowledge it internally and wait for a better moment\n"
        "- ignore: ignore it if it is irrelevant or already handled\n"
        "- wait: take no action\n\n"
        "Do not repeat the same action as the last tick unless there is new relevant state.\n"
        "If the note asks for real-world data like time or weather, use a tool this tick.\n"
        "When reporting time, prefer the tool result's display field exactly if it exists.\n"
    )


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

    if max_turns <= 0:
        print("max-turns must be greater than 0.", file=sys.stderr)
        return 2

    if interval < 0:
        print("interval must be 0 or greater.", file=sys.stderr)
        return 2

    prompt = str(getattr(args, "prompt", DEFAULT_LOOP_PROMPT) or DEFAULT_LOOP_PROMPT).strip()
    if prompt == "":
        print("prompt cannot be empty.", file=sys.stderr)
        return 2

    print("AutoRoh loop starting.")
    print(f"conversation: {conversation_id or '(new)'}")
    print(f"max_turns: {max_turns}")
    print(f"interval: {interval}")
    print(f"tools: {bool(args.tools)}")
    if args.tools:
        print(f"tool_backend: {args.tool_backend}")
        print(f"toolkit: {args.toolkit}")
    print("")

    try:
        for turn_index in range(max_turns):
            print(f"[AutoRoh turn {turn_index + 1}/{max_turns}]")

            latest_note_index: Optional[int] = None
            tick_prompt = prompt

            if conversation_id is not None:
                state = load_loop_state(ctx, conversation_id)
                latest_note_index, latest_note = _latest_unhandled_note(
                    ctx,
                    conversation_id,
                    int(state.get("last_human_note_index", -1)),
                )
                tick_prompt = _build_tick_prompt(prompt, state, latest_note)

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

            if turn_index < max_turns - 1 and interval > 0:
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
