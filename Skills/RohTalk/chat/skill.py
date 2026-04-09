"""RohTalk.chat skill.

This skill appends a user message to an existing RohTalk conversation
and runs one model turn.  The reply is printed to standard output.

If the specified conversation does not exist, a clear error message
is printed to stderr and a non‑zero exit code is returned.

Flags:

* ``--model`` – Optional model override.
* ``--host`` – Optional backend URL override.

The first positional argument is the conversation identifier.  All
subsequent positional arguments (after the ``--`` delimiter when
needed) are joined into the message text.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.RohTalk import run_conversation
from Core.LLMClient.types import LLMClientError


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for the RohTalk chat skill."""
    parser.add_argument(
        "conversation_id",
        help="Identifier of the existing conversation to append to",
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
        "message",
        nargs=argparse.REMAINDER,
        help="Message to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the chat skill: append a message to a conversation and print the reply."""
    # Combine the message tokens, dropping a leading '--' if present
    tokens: List[str] = []
    if hasattr(args, "message") and args.message:
        tokens = list(args.message)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
    user_text: str = " ".join(str(t) for t in tokens).strip()
    if user_text == "":
        print("Missing message text.", file=sys.stderr)
        return 2
    # Conversation id is required; argparse ensures it is present
    conv_id: str = str(args.conversation_id)

    try:
        _conv_id, reply = run_conversation(
            ctx,
            user_text,
            conversation_id=conv_id,
            model=args.model,
            host=args.host,
        )
    except FileNotFoundError as exc:
        # Conversation does not exist
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
    
