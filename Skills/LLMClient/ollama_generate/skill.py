"""LLMClient.ollama_generate skill.

This skill is a thin wrapper around the `Core.LLMClient` API.  It
accepts a plain prompt and forwards it to a locally running Ollama
server.  On success it prints the generated response to stdout and
returns a zero exit code.  On failure it prints a concise error
message to stderr and returns a non‑zero exit code.

Flags:

* ``--host`` – Optional base URL for the Ollama server.  Defaults to
  ``http://localhost:11434`` when omitted.
* ``--model`` – Required model name.  You must have pulled this model
  with `ollama pull` beforehand.
* ``--timeout`` – Optional timeout in seconds.  If the request takes
  longer than this the skill aborts and returns an error.

Any positional arguments after the flags are joined into a single
prompt string.  Use `--` to separate the prompt from the preceding
flags if the prompt itself begins with dashes.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, List

from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import LLMClientError


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the given parser with arguments for the Ollama generate skill."""
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
        help="Prompt to send to the model (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the skill: send a prompt to Ollama and print the result."""
    # Gather and join the prompt tokens.  argparse.REMAINDER may include
    # the '--' delimiter when present so drop it if found.
    tokens: List[str] = []
    if hasattr(args, "prompt") and args.prompt:
        tokens = list(args.prompt)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
    prompt: str = " ".join(str(t) for t in tokens).strip()

    client = LLMClient(http_post=None)
    try:
        # Pass through optional parameters; model may be None which
        # triggers a helpful error in LLMClient
        response = client.generate(
            prompt,
            model=args.model,
            host=args.host,
            timeout_s=args.timeout,
        )
    except LLMClientError as exc:
        # Print the error message to stderr and return a non‑zero code
        print(str(exc), file=sys.stderr)
        return 1

    # Print the response (if any) to stdout; always return 0
    if response:
        print(response)
    return 0
    