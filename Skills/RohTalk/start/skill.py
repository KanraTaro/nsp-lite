"""RohTalk.start skill.

This skill starts a new persistent RohTalk conversation, runs the first
model turn, and prints the new conversation id along with the assistant
reply.

If --title is omitted, the conversation title is derived automatically
from the first user message.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import run_conversation


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for starting a conversation."""
    parser.add_argument(
        "--title",
        dest="title",
        default=None,
        help="Optional conversation title",
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="Optional model override",
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=None,
        help="Optional backend URL override",
    )
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="First message to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Start a new persistent conversation and print the id and reply."""
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]

    user_text: str = " ".join(str(token) for token in tokens).strip()
    if user_text == "":
        print("Missing prompt text.", file=sys.stderr)
        return 2

    try:
        conversation_id, reply = run_conversation(
            ctx,
            user_text,
            conversation_id=None,
            kind="conversation",
            model=args.model,
            host=args.host,
            title=args.title,
        )
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    title_text = str(args.title).strip() if args.title is not None and str(args.title).strip() != "" else "(auto)"
    print(f"conversation_id: {conversation_id}")
    print(f"title: {title_text}")
    if reply:
        print(reply)
    return 0
