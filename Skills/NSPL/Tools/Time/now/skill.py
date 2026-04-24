"""NSPL.Tools.Time.now skill.

Print the current time in a structured, model-friendly format.

By default this returns the machine's local time plus UTC time. When
ctx.json is enabled, it emits JSON so Roh can use the result without
guessing timezone math.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from typing import Any, Dict


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--timezone",
        "--tz",
        dest="timezone_name",
        default=None,
        help="Optional IANA timezone name, e.g. America/New_York",
    )


def _load_timezone(timezone_name: str | None) -> _dt.tzinfo:
    if timezone_name is None or str(timezone_name).strip() == "":
        return _dt.datetime.now().astimezone().tzinfo or _dt.UTC

    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(str(timezone_name).strip())
    except Exception as exc:
        raise ValueError(f"Invalid timezone: {timezone_name}") from exc


def _format_offset(value: _dt.datetime) -> str:
    offset = value.utcoffset()
    if offset is None:
        return "+00:00"

    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return f"{sign}{hours:02d}:{minutes:02d}"


def _build_payload(timezone_name: str | None) -> Dict[str, Any]:
    target_tz = _load_timezone(timezone_name)

    utc_now = _dt.datetime.now(_dt.UTC).replace(microsecond=0)
    local_now = utc_now.astimezone(target_tz)

    return {
        "utc_iso": utc_now.isoformat().replace("+00:00", "Z"),
        "local_iso": local_now.isoformat(),
        "date": local_now.date().isoformat(),
        "time": local_now.strftime("%H:%M:%S"),
        "weekday": local_now.strftime("%A"),
        "timezone": str(getattr(target_tz, "key", None) or local_now.tzname() or "local"),
        "timezone_abbreviation": local_now.tzname(),
        "utc_offset": _format_offset(local_now),
    }


def run(args: argparse.Namespace, ctx: Any) -> int:
    timezone_name = getattr(args, "timezone_name", None)
    payload = _build_payload(timezone_name)

    if getattr(ctx, "json", False):
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        return 0

    print(
        f"{payload['weekday']}, {payload['date']} "
        f"{payload['time']} {payload['timezone_abbreviation']} "
        f"({payload['timezone']}, UTC{payload['utc_offset']})"
    )
    return 0
