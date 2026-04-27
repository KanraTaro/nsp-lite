"""NSPL.File.read skill.

Read a file from disk.

Modes:
- text (default)
- json (--json-output)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from Core.NSPL.File.read import read_text, read_json


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "path",
        help="Path to file",
    )

    parser.add_argument(
        "--json-output",
        dest="json_output",
        action="store_true",
        help="Parse file as JSON and return structured output",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    path = str(args.path)

    try:
        if args.json_output:
            data = read_json(path)

            if getattr(ctx, "json", False):
                print(json.dumps(data, separators=(",", ":"), sort_keys=True))
            else:
                print(json.dumps(data, indent=2))

        else:
            text = read_text(path)
            print(text)

        return 0

    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
