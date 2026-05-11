"""RohTalk.start skill.

Start a new persistent RohTalk conversation and print the id and reply.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import parse_model_option_args, run_turn


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", dest="title", default=None, help="Optional conversation title")
    parser.add_argument("--model", dest="model", default=None, help="Optional model override")
    parser.add_argument("--host", dest="host", default=None, help="Optional backend URL override")
    parser.add_argument("--model-profile", dest="model_profile", default=None, help="Optional model profile name")
    parser.add_argument(
        "--model-option",
        dest="model_options",
        action="append",
        default=[],
        help="Model runtime option as key=value; repeatable",
    )
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
        "prompt",
        nargs=argparse.REMAINDER,
        help="First message to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]

    user_text = " ".join(str(token) for token in tokens).strip()
    if user_text == "":
        print("Missing prompt text.", file=sys.stderr)
        return 2

    try:
        raw_model_options = getattr(args, "model_options", [])
        conversation_id, reply = run_turn(
            ctx,
            user_text,
            conversation_id=None,
            kind="conversation",
            model=args.model,
            host=args.host,
            model_profile=getattr(args, "model_profile", None),
            model_options=parse_model_option_args(raw_model_options) if raw_model_options else None,
            title=args.title,
            use_tools=bool(args.tools),
            tool_backend=str(args.tool_backend),
            toolkit=str(args.toolkit),
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
