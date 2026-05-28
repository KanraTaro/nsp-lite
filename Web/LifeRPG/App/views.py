from __future__ import annotations

import json
from typing import Any


def parse_skill_json(result) -> dict[str, Any]:
    if result.exit_code != 0:
        return {"ok": False, "error": result.stderr or "skill failed", "result": result.as_dict()}
    try:
        payload = json.loads(result.stdout or "{}")
    except Exception as exc:
        return {"ok": False, "error": f"could not parse skill JSON: {exc}", "result": result.as_dict()}
    if isinstance(payload, dict):
        payload["ok"] = True
        return payload
    return {"ok": True, "value": payload}
