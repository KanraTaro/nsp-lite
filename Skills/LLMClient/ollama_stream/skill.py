"""LLMClient.ollama_stream skill.

This skill streams a chat request to a locally running Ollama model
using the provider‑neutral ``LLMClient.chat_stream`` API.  It accepts
a single user message and prints the model's response incrementally
to stdout.  Tool calls are not executed; if present in the stream
they are reported as separate notes.  On failure the skill prints a
concise error message to stderr and returns a non‑zero exit code.

Flags:

* ``--host`` – Optional base URL for the Ollama server.  Defaults to
  ``http://localhost:11434`` when omitted.
* ``--model`` – Required model name.  You must have pulled this model
  with `ollama pull` beforehand.
* ``--timeout`` – Optional timeout in seconds.  If the request takes
  longer than this the skill aborts and returns an error.

Any positional arguments after the flags are joined into a single
user message.  Use `--` to separate the prompt from the preceding
flags if the message itself begins with dashes.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import LLMClientError


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the given parser with arguments for the Ollama streaming skill."""
    parser.add_argument(
        "--host",
        dest="host",
        default=None,
        help="Base URL of the Ollama server (default http://localhost:11434)",
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="Model name to use (must be pulled via ollama pull)",
    )
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=float,
        default=None,
        help="Optional timeout in seconds for the request",
    )
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Message to send to the model (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the skill: stream a chat message and print the result progressively."""
    # Gather and join the prompt tokens.  argparse.REMAINDER may include
    # the '--' delimiter when present so drop it if found.
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
    user_text: str = " ".join(str(t) for t in tokens).strip()
    messages = []
    if user_text:
        messages.append({"role": "user", "content": user_text})

    client = LLMClient()
    try:
        model: str = str(args.model or "").strip()
        if model == "":
            print("Missing required --model (example: --model qwen3:0.6b)", file=sys.stderr)
            return 2

        if user_text == "":
            print("Missing prompt text.", file=sys.stderr)
            return 2

        events = client.chat_stream(
            messages,
            model=model,
            host=args.host,
            timeout_s=args.timeout,
        )
        # Iterate through stream events and print text deltas immediately.
        for event in events:
            if event.type == "text" and event.text_delta:
                print(event.text_delta, end="", flush=True)
            elif event.type == "tool_call" and event.tool_call:
                tc = event.tool_call
                print(
                    f"\n[tool_call] {tc.name} {tc.arguments_json}\n",
                    end="",
                    flush=True,
                )
        print()
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

