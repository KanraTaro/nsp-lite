"""Tools.Echo.echo skill.

This skill echoes a message back to stdout.  It mirrors the semantics
of the test Dummy.echo skill shipped with SkillCLI, but lives in the
Tools domain for consistency.  If no message is provided, nothing is
printed and success is returned.
"""

from __future__ import annotations

import argparse
from typing import Any


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser to accept an arbitrary message.

    The message positional argument is defined with ``nargs="*"`` so
    that any number of tokens after the skill name are captured.  This
    mirrors the behaviour expected by the ChatOps tests which may pass
    multiple words separated by spaces.  When no message is provided
    the default is an empty list.
    """
    parser.add_argument(
        "message",
        nargs="*",
        default=[],
        help="The message to echo back (all remaining tokens are joined)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Print the provided message and return success.

    The ``message`` attribute will be a list of strings because the
    parser uses ``nargs="*"``.  If one or more tokens were provided
    they are concatenated with single spaces before printing.  When
    no tokens are supplied nothing is printed.  The return value
    indicates success (0).
    """
    if args.message:
        # Join tokens with spaces to reconstruct the original message
        if isinstance(args.message, list):
            out = " ".join(str(part) for part in args.message).strip()
        else:
            out = str(args.message)
        if out:
            print(out)
    return 0
