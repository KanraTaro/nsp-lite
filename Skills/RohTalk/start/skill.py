"""RohTalk.start skill.

This skill starts a new persistent RohTalk conversation, runs the first
model turn, and prints the new conversation id along with the assistant
reply.

If --title is omitted, the conversation title is derived automatically
from the first user message.

When --tools is enabled, the first turn is executed through the
tool-capable RohTalk loop and the resulting normalized history is
persisted back into the conversation.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

from Core.LLMClient.types import LLMClientError, ToolDef
from Core.RohTalk import load_config, run_conversation, update_conversation_messages
from Core.RohTalk.conversations import create_conversation, get_conversation
from Core.RohTalk.tool_loop import run_tool_loop


def _get_weather(city: str) -> Dict[str, Any]:
    return {
        "city": city,
        "forecast": "Partly cloudy",
        "temp_f": 82,
    }


TOOLS: List[ToolDef] = [
    ToolDef(
        name="get_weather",
        description="Get the weather for a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
            },
            "required": ["city"],
        },
    )
]


TOOL_IMPL = {
    "get_weather": _get_weather,
}


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
        "--tools",
        dest="tools",
        action="store_true",
        help="Enable tool loop for this conversation",
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
        if not args.tools:
            conversation_id, reply = run_conversation(
                ctx,
                user_text,
                conversation_id=None,
                kind="conversation",
                model=args.model,
                host=args.host,
                title=args.title,
            )
        else:
            config = load_config(ctx)
            model = args.model or config.default_model
            host = args.host or config.default_host

            conversation_id, _ = create_conversation(
                ctx,
                user_text,
                kind="conversation",
                model=model,
                host=host,
                title=args.title,
                skip_model=True,
            )

            metadata = get_conversation(ctx, conversation_id)
            messages = list(metadata.get("messages", []))

            reply, final_messages = run_tool_loop(
                messages,
                model=model,
                host=host,
                tools=TOOLS,
                tool_impl=TOOL_IMPL,
                max_steps=5,
            )

            update_conversation_messages(
                ctx,
                conversation_id,
                final_messages,
                model=model,
                host=host,
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
