"""RohTalk.shell skill.

Interactive terminal shell for a persistent RohTalk conversation.

Design goals:
- create or attach to a conversation
- reload conversation state before each turn
- allow outside writers to update the same conversation
- optionally run tool-capable turns through Core.RohTalk.run_turn
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from Core.LLMClient.types import LLMClientError
from Core.RohTalk import (
    get_conversation,
    list_conversations,
    run_turn,
)


def _resolve_conversation_id(ctx: Any, raw_value: str) -> str:
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


def _get_messages(ctx: Any, conversation_id: str) -> List[Dict[str, Any]]:
    metadata = get_conversation(ctx, conversation_id)
    messages = metadata.get("messages", [])
    if not isinstance(messages, list):
        return []

    result: List[Dict[str, Any]] = []
    for message in messages:
        if isinstance(message, dict):
            result.append(message)
    return result


def _latest_message_count(ctx: Any, conversation_id: str) -> int:
    return len(_get_messages(ctx, conversation_id))


def _format_message(message: Dict[str, Any], *, external: bool = False) -> str:
    role = str(message.get("role", "unknown"))
    content = str(message.get("content", "") or "").strip()
    prefix = "external " if external else ""

    if content == "" and role == "assistant" and message.get("tool_calls"):
        tool_calls = message.get("tool_calls")
        lines = [f"[{prefix}assistant]", "<tool call requested>"]

        if isinstance(tool_calls, list):
            for item in tool_calls:
                if not isinstance(item, dict):
                    continue

                name = str(item.get("name", "") or "").strip()
                call_id = str(item.get("id", "") or "").strip()
                arguments = item.get("arguments", {})
                lines.append(
                    f"[tool_call:{name}] id={call_id} args="
                    f"{json.dumps(arguments, separators=(',', ':'), sort_keys=True)}"
                )

        return "\n".join(lines)

    if role == "tool":
        tool_name = str(message.get("tool_name", "") or "").strip()
        tool_call_id = str(message.get("tool_call_id", "") or "").strip()
        header = f"[{prefix}tool]"
        details: List[str] = []

        if tool_name:
            details.append(f"tool_name: {tool_name}")
        if tool_call_id:
            details.append(f"tool_call_id: {tool_call_id}")
        if content:
            details.append(content)

        return header + "\n" + "\n".join(details)

    if content == "":
        return ""

    return f"[{prefix}{role}]\n{content}"


def _print_messages(messages: List[Dict[str, Any]], *, external: bool = False) -> None:
    for message in messages:
        rendered = _format_message(message, external=external)
        if rendered.strip() == "":
            continue
        print("")
        print(rendered)


def _print_recent(ctx: Any, conversation_id: str, count: int) -> None:
    messages = _get_messages(ctx, conversation_id)
    if not messages:
        print("(no messages)")
        return

    count = max(1, count)
    _print_messages(messages[-count:])


def _print_history(ctx: Any, conversation_id: str) -> None:
    messages = _get_messages(ctx, conversation_id)
    if not messages:
        print("(no messages)")
        return

    _print_messages(messages)


def _print_new_external_messages(ctx: Any, conversation_id: str, seen_count: int) -> int:
    messages = _get_messages(ctx, conversation_id)

    if len(messages) <= seen_count:
        return len(messages)

    new_messages = messages[seen_count:]
    _print_messages(new_messages, external=True)
    return len(messages)


def _print_step(step_index: int) -> None:
    print(f"[step {step_index + 1}]", file=sys.stderr)


def _print_text_delta(text: str) -> None:
    print(text, end="", flush=True)


def _print_tool_call(tool_call: Any) -> None:
    arguments = getattr(tool_call, "arguments", {})
    print(
        f"\n[tool_call] {getattr(tool_call, 'name', '')} "
        f"{json.dumps(arguments, separators=(',', ':'), sort_keys=True)}",
        file=sys.stderr,
    )


def _print_tool_result(tool_result: Dict[str, Any]) -> None:
    print(
        f"[tool_result] {json.dumps(tool_result, separators=(',', ':'), sort_keys=True)}",
        file=sys.stderr,
    )


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--conversation",
        "--conversation-id",
        dest="conversation_ref",
        default=None,
        help="Existing conversation id or numeric index from RohTalk.list_conversations",
    )
    parser.add_argument(
        "--title",
        dest="title",
        default=None,
        help="Optional title when creating a new conversation",
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
        "--show-history",
        dest="show_history",
        action="store_true",
        help="Print full conversation history when attaching",
    )
    parser.add_argument(
        "--recent-count",
        dest="recent_count",
        type=int,
        default=8,
        help="Number of messages shown by /recent",
    )
    parser.add_argument(
        "--tools",
        dest="tools",
        action="store_true",
        help="Enable tool-capable turns",
    )
    parser.add_argument(
        "--tool-backend",
        dest="tool_backend",
        choices=["skillcli", "local"],
        default="skillcli",
        help="Tool execution backend when --tools is enabled",
    )
    parser.add_argument(
        "--tool-trace",
        dest="tool_trace",
        action="store_true",
        help="Print tool calls and tool results during tool-capable turns",
    )
    parser.add_argument(
        "--toolkit",
        dest="toolkit",
        default="basic",
        help="Tool kit to expose when --tools is enabled",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    conversation_id: Optional[str] = None
    seen_count = 0
    recent_count = max(1, int(getattr(args, "recent_count", 8) or 8))

    try:
        if args.conversation_ref:
            conversation_id = _resolve_conversation_id(ctx, args.conversation_ref)
            metadata = get_conversation(ctx, conversation_id)
            seen_count = _latest_message_count(ctx, conversation_id)

            title = str(metadata.get("title", "") or "").strip()
            print(f"Attached to conversation: {conversation_id}")
            if title:
                print(f"Title: {title}")

            if args.show_history:
                _print_history(ctx, conversation_id)
        else:
            print("Starting new RohTalk shell conversation.")
            print("First message will create the conversation.")

    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("")
    print("Commands:")
    print("  /exit, /quit     leave shell")
    print("  /id              show current conversation id")
    print("  /refresh         show messages added externally")
    print("  /recent          show recent conversation messages")
    print("  /history         show full conversation history")
    print("")

    if args.tools:
        print(f"Tools: enabled ({args.tool_backend}, toolkit={args.toolkit})")
        print("")

    while True:
        try:
            user_text = input("roh> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return 0

        if user_text == "":
            continue

        if user_text in {"/exit", "/quit"}:
            return 0

        if user_text == "/id":
            print(conversation_id or "(no conversation yet)")
            continue

        if user_text == "/refresh":
            if conversation_id is None:
                print("(no conversation yet)")
                continue
            seen_count = _print_new_external_messages(ctx, conversation_id, seen_count)
            continue

        if user_text == "/recent":
            if conversation_id is None:
                print("(no conversation yet)")
                continue
            _print_recent(ctx, conversation_id, recent_count)
            continue

        if user_text == "/history":
            if conversation_id is None:
                print("(no conversation yet)")
                continue
            _print_history(ctx, conversation_id)
            continue

        try:
            if conversation_id is not None:
                seen_count = _print_new_external_messages(ctx, conversation_id, seen_count)

            conversation_id, reply = run_turn(
                ctx,
                user_text,
                conversation_id=conversation_id,
                kind="conversation",
                model=args.model,
                host=args.host,
                title=args.title,
                use_tools=bool(args.tools),
                tool_backend=str(args.tool_backend),
                on_text_delta=_print_text_delta if args.tools else None,
                on_step=_print_step if args.tools and args.tool_trace else None,
                on_tool_call=_print_tool_call if args.tools and args.tool_trace else None,
                on_tool_result=_print_tool_result if args.tools and args.tool_trace else None,
                toolkit=str(args.toolkit),
            )

            if args.tools:
                if not reply:
                    print("(empty reply)")
                else:
                    print("")
            elif reply:
                print(reply)

            seen_count = _latest_message_count(ctx, conversation_id)

        except LLMClientError as exc:
            print(str(exc), file=sys.stderr)
        except Exception as exc:
            print(str(exc), file=sys.stderr)

    return 0
