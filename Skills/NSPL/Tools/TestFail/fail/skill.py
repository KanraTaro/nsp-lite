"""Tools.TestFail.fail skill.

This skill is designed to fail with a non-zero exit code.  It can be used
to verify that ChatOps correctly handles failing tasks.
"""

from __future__ import annotations

import argparse
from typing import Any


def build_parser(parser: argparse.ArgumentParser) -> None:
    # No custom arguments for this test skill
    parser.add_argument(
        "--message",
        default="",
        help="Optional message to emit on stdout before failing",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    # Print the message if provided
    if getattr(args, "message", ""):
        print(args.message)
    # Return non-zero to indicate failure
    return 1
