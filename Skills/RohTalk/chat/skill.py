"""RohTalk.chat skill.

This skill appends a user message to an existing RohTalk conversation
and runs one model turn. The reply is printed to standard output.

The conversation reference may be either:
- a full conversation id
- a numeric index from RohTalk.list_conversations output

If the specified conversation does not exist, a clear error message
is printed to stderr and a non-zero exit code is returned.

Flags:

* ``--model`` - Optional model override.
* ``--host`` - Optional backend URL override.
* ``--tools`` - Enable tool-capable loop for this message.

The first positional argument is the conversation identifier or numeric
list index. All subsequent positional arguments after the optional
``--`` delimiter are joined into the message text.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import (
    list_conversations,
    load_config,
    run_conversation,
    update_conversation_messages,
)
from Core.RohTalk.conversations import get_conversation
from Core.RohTalk.local_tools import LOCAL_TOOLS, LOCAL_TOOL_IMPL
from Core.RohTalk.tool_loop import run_tool_loop


def _resolve_conversation_id(ctx: Any, raw_value: str) -> str:
    """Resolve either a conversation id or a numeric list index."""
    text = str(raw_value).strip()
    if text == "":
        raise ValueError("Missing conversation identifier.")

    if text.isdigit():
        index = int(text)
        conversations: List[Dict[str, Any]] = list_conversations(ctx, include_oneshots=False)
        if index < 0 or index >= len(conversations):
            raise IndexError(f"Conversation index {index} is out of range.")
        return str(conversations[index].get("id", ""))

    return text


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for the RohTalk chat skill."""
    parser.add_argument(
        "conversation_ref",
        help="Conversation id or numeric index from RohTalk.list_conversations",
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
        "--tools",
        dest="tools",
        action="store_true",
        help="Enable tool loop for this message",
    )
    parser.add_argument(
        "message",
        nargs=argparse.REMAINDER,
        help="Message to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the chat skill: append a message to a conversation and print the reply."""
    tokens: List[str] = []
    if hasattr(args, "message") and args.message:
        tokens = list(args.message)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]

    user_text: str = " ".join(str(token) for token in tokens).strip()
    if user_text == "":
        print("Missing message text.", file=sys.stderr)
        return 2

    try:
        conversation_id = _resolve_conversation_id(ctx, args.conversation_ref)

        if not args.tools:
            _conv_id, reply = run_conversation(
                ctx,
                user_text,
                conversation_id=conversation_id,
                model=args.model,
                host=args.host,
            )
        else:
            config = load_config(ctx)
            model = args.model or config.default_model
            host = args.host or config.default_host

            metadata = get_conversation(ctx, conversation_id)
            messages = list(metadata.get("messages", []))
            messages.append(
                {
                    "role": "user",
                    "content": user_text,
                }
            )

            reply, final_messages = run_tool_loop(
                messages,
                model=model,
                host=host,
                tools=LOCAL_TOOLS,
                tool_impl=LOCAL_TOOL_IMPL,
                max_steps=5,
            )

            update_conversation_messages(
                ctx,
                conversation_id,
                final_messages,
                model=model,
                host=host,
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
