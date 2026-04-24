"""RohTalk.tool_test skill.

This is a proving skill for the RohTalk tool loop.

It can run against either:
- shared local in-process tools
- SkillCLI-backed tools executed in-process through the SkillCLI loader

This skill does NOT persist conversations. It is intended purely as a
runtime smoke test for tool calling.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from Core.LLMClient.types import ToolDef
from Core.RohTalk import load_config, run_tool_loop
from Core.RohTalk.local_tools import LOCAL_TOOLS, LOCAL_TOOL_IMPL
from Core.RohTalk.skillcli_tools import (
    build_tool_name_map,
    canonical_skill_name_to_tool_name,
    execute_skill,
)


SKILLCLI_SKILL_NAMES: List[str] = [
    "NSPL.Tools.Weather.get",
    "NSPL.Tools.Time.now",
]

SKILLCLI_TOOLS: List[ToolDef] = [
    ToolDef(
        name=canonical_skill_name_to_tool_name("NSPL.Tools.Weather.get"),
        description=(
            "Get the weather for a city. "
            "Use this when the user asks about weather in a specific place."
        ),
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to get weather for",
                }
            },
            "required": ["city"],
        },
    ),
    ToolDef(
        name=canonical_skill_name_to_tool_name("NSPL.Tools.Time.now"),
        description=(
            "Get the current time. "
            "Use this when the user asks for the current time or date."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]

SKILLCLI_TOOL_NAME_MAP: Dict[str, str] = build_tool_name_map(SKILLCLI_SKILL_NAMES)


def _print_step(step_index: int) -> None:
    print(f"[step {step_index + 1}]", file=sys.stderr)


def _print_text_delta(text: str) -> None:
    print(text, end="", file=sys.stderr, flush=True)


def _print_assistant_message(message: Dict[str, Any]) -> None:
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list) and len(tool_calls) > 0:
        print("\n[assistant requested tool call(s)]", file=sys.stderr)
        return

    content = str(message.get("content", "") or "")
    if content.strip() == "":
        print("\n[assistant text] <empty>", file=sys.stderr)
    else:
        print("", file=sys.stderr)


def _print_tool_call(tool_call: Any) -> None:
    arguments = getattr(tool_call, "arguments", {})
    print(
        f"[tool_call] {getattr(tool_call, 'name', '')} {json.dumps(arguments, separators=(',', ':'), sort_keys=True)}",
        file=sys.stderr,
    )


def _print_tool_result(tool_result: Dict[str, Any]) -> None:
    print(
        f"[tool_result] {json.dumps(tool_result, separators=(',', ':'), sort_keys=True)}",
        file=sys.stderr,
    )


def build_parser(parser: argparse.ArgumentParser) -> None:
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
        help="Optional backend host override",
    )
    parser.add_argument(
        "--tool-backend",
        dest="tool_backend",
        choices=["local", "skillcli"],
        default="local",
        help="Tool execution backend to use (default: local)",
    )
    parser.add_argument(
        "--show-history",
        dest="show_history",
        action="store_true",
        help="Print final normalized message history",
    )
    parser.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress streaming output and only print final response",
    )
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Prompt to send (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]

    user_text = " ".join(tokens).strip()
    if user_text == "":
        print("Missing prompt text.", file=sys.stderr)
        return 2

    try:
        config = load_config(ctx)
        model = args.model or config.default_model
        host = args.host or config.default_host

        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Use tools when helpful. "
                    "After receiving tool results, respond normally."
                ),
            },
            {
                "role": "user",
                "content": user_text,
            },
        ]

        callback_kwargs: Dict[str, Any] = {}
        if not args.quiet:
            callback_kwargs = {
                "on_step": _print_step,
                "on_text_delta": _print_text_delta,
                "on_assistant_message": _print_assistant_message,
                "on_tool_call": _print_tool_call,
                "on_tool_result": _print_tool_result,
            }

        if args.tool_backend == "local":
            final_text, final_messages = run_tool_loop(
                messages,
                model=model,
                host=host,
                tools=LOCAL_TOOLS,
                tool_impl=LOCAL_TOOL_IMPL,
                execution_mode="local",
                ctx=ctx,
                max_steps=5,
                **callback_kwargs,
            )
        else:
            final_text, final_messages = run_tool_loop(
                messages,
                model=model,
                host=host,
                tools=SKILLCLI_TOOLS,
                tool_impl=None,
                execution_mode="skillcli",
                ctx=ctx,
                skill_name_map=SKILLCLI_TOOL_NAME_MAP,
                skill_executor=execute_skill,
                max_steps=5,
                **callback_kwargs,
            )

    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        if final_text:
            print(final_text)
        else:
            print("<empty final response>", file=sys.stderr)
    else:
        print("", file=sys.stderr)

    if args.show_history:
        print("\n=== FINAL HISTORY ===\n")
        for message in final_messages:
            print(message)

    return 0
