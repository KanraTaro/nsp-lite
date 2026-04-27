"""NSPL Core File.read utilities.

Raw filesystem access helpers.

Keep this layer dumb:
- no domain logic
- no assumptions about file meaning
- just safe, explicit reads
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def read_text(path: str) -> str:
    p = Path(path).expanduser()

    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not p.is_file():
        raise ValueError(f"Not a file: {path}")

    # I want explicit encoding, no guessing later
    return p.read_text(encoding="utf-8")


def read_json(path: str) -> Dict[str, Any]:
    raw = read_text(path)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file: {path}") from exc
