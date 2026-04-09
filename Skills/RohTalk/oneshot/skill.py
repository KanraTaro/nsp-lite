"""RohTalk.oneshot skill.

This skill executes a single prompt through the RohTalk conversation
pipeline without creating a long‑lived chat session.  The user’s
prompt is persisted as a conversation with kind ``oneshot`` for audit
purposes, but oneshots are hidden from the default conversation list.
The assistant’s reply is printed to standard output.

Flags:

* ``--model`` – Optional model override.  If omitted the RohTalk
  configuration is consulted.
* ``--host`` – Optional backend URL.  Overrides the configured
  default host.

Any positional arguments after the flags are joined into a single
prompt.  Use ``--`` to separate the prompt from preceding flags if
the message begins with dashes.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.RohTalk import run_conversation
from Core.LLMClient.types import LLMClientError


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the given parser with arguments for the RohTalk oneshot skill."""
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="Override the default model (optional)",
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=None,
        help="Override the backend host URL (optional)",
    )
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Prompt to send to the assistant (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the oneshot skill: send a single prompt and print the reply."""
    # Gather and join the prompt tokens.  argparse.REMAINDER may include
    # the '--' delimiter when present so drop it if found.
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
    user_text: str = " ".join(str(t) for t in tokens).strip()
    if user_text == "":
        print("Missing prompt text.", file=sys.stderr)
        return 2

    try:
        # Run a single turn with kind=oneshot.  The runner returns (id, reply)
        _conv_id, reply = run_conversation(
            ctx,
            user_text,
            conversation_id=None,
            kind="oneshot",
            model=args.model,
            host=args.host,
        )
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        # Propagate other exceptions (e.g. config or NodeCTX) as user‑visible errors
        print(str(exc), file=sys.stderr)
        return 1

    # Print the assistant’s reply
    if reply:
        print(reply)
    return 0
    
