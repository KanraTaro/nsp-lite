"""NSPL.File.write skill.

Write text or JSON content to disk.

This is generic raw file output. Domain-specific skills should wrap
this instead of duplicating write logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from Core.NSPL.File.write import write_json, write_text


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "path",
        help="Path to write",
    )
    parser.add_argument(
        "content",
        nargs=argparse.REMAINDER,
        help="Content to write. Use -- before content when needed.",
    )
    parser.add_argument(
        "--json-input",
        dest="json_input",
        action="store_true",
        help="Parse content as JSON before writing",
    )
    parser.add_argument(
        "--pretty",
        dest="pretty",
        action="store_true",
        help="Pretty-print JSON output when --json-input is used",
    )
    parser.add_argument(
        "--no-create-parents",
        dest="create_parents",
        action="store_false",
        default=True,
        help="Do not create parent directories",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    tokens = list(getattr(args, "content", []) or [])

    json_input = bool(getattr(args, "json_input", False))
    pretty = bool(getattr(args, "pretty", False))
    create_parents = bool(getattr(args, "create_parents", True))

    clean_tokens = []
    for token in tokens:
        text = str(token)

        if text == "--":
            continue

        if text == "--json-input":
            json_input = True
            continue

        if text == "--pretty":
            pretty = True
            continue

        if text == "--no-create-parents":
            create_parents = False
            continue

        clean_tokens.append(text)

    content = " ".join(clean_tokens).strip()

    if content == "":
        print("Missing content.", file=sys.stderr)
        return 2

    try:
        if json_input:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("JSON input must be an object/dict.")

            written_path = write_json(
                str(args.path),
                data,
                create_parents=create_parents,
                pretty=pretty,
            )
        else:
            written_path = write_text(
                str(args.path),
                content,
                create_parents=create_parents,
            )

        if getattr(ctx, "json", False):
            print(json.dumps({"ok": True, "path": written_path}, separators=(",", ":"), sort_keys=True))
        else:
            print(f"wrote: {written_path}")

        return 0

    except Exception as exc:
        if getattr(ctx, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)
        return 1
