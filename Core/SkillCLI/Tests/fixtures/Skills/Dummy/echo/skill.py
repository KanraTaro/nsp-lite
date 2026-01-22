"""A simple echo skill used for testing SkillCLI.

This skill demonstrates the minimum contract for a RohTalk skill.  It
defines a ``build_parser`` function to register its own argument
(``message``) and a ``run`` function that prints the message to stdout.

Metadata is provided in ``skill.json`` rather than the ``SKILL_META``
variable because SkillCLI reads the JSON file during discovery.
"""

from __future__ import annotations

import argparse
from typing import Any

# Optional SKILL_META; mirrors skill.json for demonstration.  Not used
# during discovery but can be helpful for runtime introspection.
SKILL_META = {
    "name": "Dummy.echo",
    "version": "0.1.0",
    "description": "Echo a message back to the user",
}


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the given parser with a single positional argument."""
    parser.add_argument(
        "message",
        nargs="?",
        default="",
        help="The message to echo back",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Print the provided message and return success.

    If no message is supplied, nothing is printed.  The return value
    indicates success (0).
    """
    # Do not write to disk; just print to stdout
    if args.message:
        # Print returns None; ensure flush to help capture in tests
        print(args.message)
    return 0


if __name__ == "__main__":  # pragma: no cover
    # When executed directly, provide a minimal CLI that echoes the message.
    import argparse as _argparse
    parser = _argparse.ArgumentParser(prog="Dummy.echo", description=SKILL_META.get("description"))
    build_parser(parser)
    parsed = parser.parse_args()
    # We pass None for ctx here because direct invocation does not
    # bootstrap the full SkillCLI context.  Real skills may choose
    # to construct their own context or behave differently when
    # executed directly.
    run(parsed, None)
