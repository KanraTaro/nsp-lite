from __future__ import annotations


def clean_text(value: str | None) -> str:
    return str(value or "").strip()
