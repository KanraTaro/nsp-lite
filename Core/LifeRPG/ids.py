from __future__ import annotations

import hashlib
from typing import Any


def make_id(prefix: str, *parts: Any) -> str:
    seed = "|".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"
