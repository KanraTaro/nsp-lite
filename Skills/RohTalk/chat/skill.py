"""RohTalk.chat skill.

Append a user message to an existing RohTalk conversation and run one turn.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import resolve_conversation_ref, run_turn
from Core.RohTalk.tracing import print_step, print_tool_call, print_tool_result


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "conversation_ref",
        help="Conversation id or numeric index from RohTalk.list_conversations",
    )
    parser.add_argument("--model", dest="model", default=None, help="Optional model override")
    parser.add_argument("--host", dest="host", default=None, help="Optional backend URL override")
    parser.add_argument("--tools", dest="tools", action="store_true", help="Enable tool-capable turn")
    parser.add_argument(
        "--tool-backend",
        dest="tool_backend",
        choices=["skillcli", "local"],
        default="skillcli",
        help="Tool execution backend when --tools is enabled",
    )
    parser.add_argument(
        "--toolkit",
        dest="toolkit",
        default="basic",
        help="Tool kit to expose when --tools is enabled",
    )
    parser.add_argument(
        "--tool-trace",
        dest="tool_trace",
        action="store_true",
        help="Print tool calls and tool results during tool-capable turns",
    )
    parser.add_argument(
        "message",
        nargs=argparse.REMAINDER,
        help="Message to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    tokens: List[str] = []
    if hasattr(args, "message") and args.message:
        tokens = list(args.message)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]

    user_text = " ".join(str(token) for token in tokens).strip()
    if user_text == "":
        print("Missing message text.", file=sys.stderr)
        return 2

    try:
        conversation_id = resolve_conversation_ref(ctx, args.conversation_ref)
        use_tool_trace = bool(args.tools) and bool(getattr(args, "tool_trace", False))
        callback_kwargs = {}
        if use_tool_trace:
            callback_kwargs = {
                "on_step": print_step,
                "on_tool_call": print_tool_call,
                "on_tool_result": print_tool_result,
            }

        _conv_id, reply = run_turn(
            ctx,
            user_text,
            conversation_id=conversation_id,
            kind="conversation",
            model=args.model,
            host=args.host,
            title=None,
            use_tools=bool(args.tools),
            tool_backend=str(args.tool_backend),
            toolkit=str(args.toolkit),
            **callback_kwargs,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (ValueError, IndexError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if reply:
        print(reply)

    return 0
