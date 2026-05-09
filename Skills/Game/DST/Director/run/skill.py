"""Game.DST.Director.run skill."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Optional

from Core.AutoRoh.loop_runner import AutoRohLoopConfig, run_autoroh_loop
from Core.AutoRoh.observations import call_observation_tool
from Core.RohTalk import create_conversation, resolve_conversation_ref


DST_DIRECTOR_SEED_PROMPT = (
    "You are Roh, running as a live Don't Starve Together director. "
    "Observe the world, keep guidance concise, and use director tools when useful."
)


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--conversation",
        "--conversation-id",
        dest="conversation_ref",
        default=None,
        help="Existing RohTalk conversation id, short id, or numeric index.",
    )
    parser.add_argument(
        "--title",
        dest="title",
        default="DST Director",
        help="Title when creating a new conversation.",
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        type=float,
        default=10.0,
        help="Seconds to wait between director ticks.",
    )
    parser.add_argument(
        "--max-turns",
        dest="max_turns",
        type=int,
        default=None,
        help="Bounded test mode. If provided, the director does not run forever.",
    )
    parser.add_argument(
        "--once",
        dest="max_turns",
        action="store_const",
        const=1,
        help="Run one director tick.",
    )
    parser.add_argument(
        "--no-tool-trace",
        dest="tool_trace",
        action="store_false",
        default=True,
        help="Disable tool trace output.",
    )
    parser.add_argument(
        "--no-idle-skip",
        dest="idle_skip",
        action="store_false",
        default=True,
        help="Force model ticks even when observation state is unchanged.",
    )
    parser.add_argument(
        "--skip-checks",
        dest="skip_checks",
        action="store_true",
        help="Skip snapshot_read preflight.",
    )
    parser.add_argument("--model", dest="model", default=None, help="Optional model override.")
    parser.add_argument("--host", dest="host", default=None, help="Optional backend URL override.")


def _print_shell_command(
    conversation_id: str,
    model: str | None = None,
    host: str | None = None,
) -> None:
    command_parts = [
        "shell: nspl-skill skill RohTalk.shell",
        f"--conversation {conversation_id}",
        "--tools",
        "--toolkit dst_director",
        "--tool-trace",
    ]
    if model:
        command_parts.append(f"--model {model}")
    if host:
        command_parts.append(f"--host {host}")
    print(
        " ".join(command_parts)
    )


def _resolve_or_create_conversation(args: argparse.Namespace, ctx: Any) -> Optional[str]:
    if args.conversation_ref:
        return resolve_conversation_ref(ctx, args.conversation_ref)

    conversation_id, _reply = create_conversation(
        ctx,
        DST_DIRECTOR_SEED_PROMPT,
        kind="conversation",
        model=getattr(args, "model", None),
        host=getattr(args, "host", None),
        title=str(getattr(args, "title", "DST Director") or "DST Director"),
        skip_model=True,
    )
    return conversation_id


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        conversation_id = _resolve_or_create_conversation(args, ctx)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not conversation_id:
        print("Unable to resolve or create a conversation.", file=sys.stderr)
        return 1

    print(f"conversation_id: {conversation_id}")
    _print_shell_command(
        conversation_id,
        model=getattr(args, "model", None),
        host=getattr(args, "host", None),
    )

    if not bool(getattr(args, "skip_checks", False)):
        try:
            call_observation_tool(
                ctx,
                toolkit_name="dst_director",
                tool_name="snapshot_read",
            )
        except Exception as exc:
            print(f"snapshot_read preflight failed: {exc}", file=sys.stderr)
            return 1

    max_turns = getattr(args, "max_turns", None)
    forever = max_turns is None
    bounded_max_turns = 5 if max_turns is None else int(max_turns)

    config = AutoRohLoopConfig(
        conversation_id=conversation_id,
        prompt=DST_DIRECTOR_SEED_PROMPT,
        interval=float(getattr(args, "interval", 10.0) or 10.0),
        max_turns=bounded_max_turns,
        forever=forever,
        title=str(getattr(args, "title", "DST Director") or "DST Director"),
        model=getattr(args, "model", None),
        host=getattr(args, "host", None),
        tools=True,
        tool_backend="skillcli",
        toolkit="dst_director",
        tool_trace=bool(getattr(args, "tool_trace", True)),
        idle_skip=bool(getattr(args, "idle_skip", True)),
        observation_tool="snapshot_read",
    )
    return run_autoroh_loop(ctx, config)
