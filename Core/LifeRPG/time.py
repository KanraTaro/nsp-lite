from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def add_minutes(value: str, minutes: int) -> str:
    return (parse_utc(value) + timedelta(minutes=int(minutes))).isoformat().replace("+00:00", "Z")


def today_key() -> str:
    return utc_now().date().isoformat()
