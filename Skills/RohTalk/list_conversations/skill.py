"""RohTalk.list_conversations skill.

This skill lists stored RohTalk conversations.  By default oneshot
conversations are omitted from the list.  Each line of output
contains the conversation identifier followed by the timestamp of
its last update.  Ordering is from oldest to newest.

Flags:

* ``--include-oneshots`` – When provided, include oneshot
  conversations in the output.
"""

from __future__ import annotations

import argparse
from typing import Any

from Core.RohTalk import list_conversations


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for listing conversations."""
    parser.add_argument(
        "--include-oneshots",
        dest="include_oneshots",
        action="store_true",
        help="Include oneshot conversations in the list",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the list_conversations skill: print stored conversations."""
    include = bool(getattr(args, "include_oneshots", False))
    try:
        convs = list_conversations(ctx, include_oneshots=include)
    except Exception as exc:
        # If something goes wrong reading metadata, surface the error
        # as a non-zero exit code and message.
        print(str(exc))
        return 1
    for meta in convs:
        conv_id = meta.get("id", "")
        ts = meta.get("updated_at", meta.get("created_at", ""))
        print(f"{conv_id} {ts}")
    return 0
    
