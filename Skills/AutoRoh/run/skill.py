"""AutoRoh.run skill."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Optional

from Core.AutoRoh.loop_runner import AutoRohLoopConfig, run_autoroh_loop
from Core.AutoRoh.prompts import DEFAULT_LOOP_PROMPT
from Core.RohTalk import resolve_conversation_ref


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
        "--forever",
        dest="forever",
        action="store_true",
        help="Run until interrupted with Ctrl+C. Ignores --max-turns.",
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
    parser.add_argument(
        "--tool-trace",
        dest="tool_trace",
        action="store_true",
        help="Print model tool calls and tool results during tool-capable turns.",
    )
    parser.add_argument(
        "--idle-skip",
        dest="idle_skip",
        action="store_true",
        help="Skip model calls when no new note and observed state has not changed.",
    )
    parser.add_argument(
        "--observation-tool",
        dest="observation_tool",
        default=None,
        help="Model-facing tool name to call before each tick, e.g. snapshot_read.",
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

    config = AutoRohLoopConfig(
        conversation_id=conversation_id,
        prompt=getattr(args, "prompt", DEFAULT_LOOP_PROMPT),
        interval=float(getattr(args, "interval", 10.0) or 10.0),
        max_turns=int(getattr(args, "max_turns", 5) or 5),
        forever=bool(getattr(args, "forever", False)),
        title=str(getattr(args, "title", "AutoRoh Loop") or "AutoRoh Loop"),
        model=getattr(args, "model", None),
        host=getattr(args, "host", None),
        tools=bool(getattr(args, "tools", False)),
        tool_backend=str(getattr(args, "tool_backend", "skillcli") or "skillcli"),
        toolkit=str(getattr(args, "toolkit", "basic") or "basic"),
        tool_trace=bool(getattr(args, "tool_trace", False)),
        idle_skip=bool(getattr(args, "idle_skip", False)),
        observation_tool=getattr(args, "observation_tool", None),
    )
    return run_autoroh_loop(ctx, config)
