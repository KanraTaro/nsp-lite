"""NSPL Core File.write utilities.

Raw filesystem write helpers.

Keep this layer dumb:
- no domain logic
- no assumptions about file meaning
- just safe, explicit writes
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_text(path: str, text: str, *, create_parents: bool = True) -> str:
    target = Path(path).expanduser()

    if create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not target.is_file():
        raise ValueError(f"Path exists but is not a file: {path}")

    target.write_text(str(text), encoding="utf-8")
    return str(target)


def write_json(
    path: str,
    data: Dict[str, Any],
    *,
    create_parents: bool = True,
    pretty: bool = False,
) -> str:
    if not isinstance(data, dict):
        raise ValueError("JSON data must be an object/dict.")

    if pretty:
        text = json.dumps(data, indent=2, sort_keys=True)
    else:
        text = json.dumps(data, separators=(",", ":"), sort_keys=True)

    return write_text(path, text, create_parents=create_parents)
