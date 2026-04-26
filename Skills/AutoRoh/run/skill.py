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
from typing import Any, Optional

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import resolve_conversation_ref, run_turn


DEFAULT_LOOP_PROMPT = (
    "AutoRoh loop tick.\n\n"
    "You must follow these rules:\n"
    "- If the task requires real-world or external data such as time, weather, files, or game state, you MUST use an available tool.\n"
    "- Do not guess, approximate, or reuse stale real-world data when a tool can check it.\n"
    "- Pay special attention to recent [human note] messages. Treat them as guidance for this tick.\n"
    "- Decide whether to wait, comment, suggest, or act.\n"
    "- If nothing meaningful changed, say that you will wait.\n"
    "- If you cannot act safely or cannot access the needed tool, say you will wait and explain briefly.\n"
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
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="Optional model override.",
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=None,
        help="Optional backend URL override.",
    )
    parser.add_argument(
        "--tools",
        dest="tools",
        action="store_true",
        help="Enable tool-capable turns.",
    )
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

            conversation_id, reply = run_turn(
                ctx,
                prompt,
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
