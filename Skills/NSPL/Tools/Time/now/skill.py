"""Tools.Time.now skill.

This simple skill prints the current UTC timestamp in ISO 8601 format.
It is useful for verifying that ChatOps can execute skills that
produce artifacts or side effects. No arguments are required.
"""

from __future__ import annotations

import argparse
import datetime as _dt
from typing import Any


def build_parser(parser: argparse.ArgumentParser) -> None:
    # No custom arguments for this skill
    pass


def run(args: argparse.Namespace, ctx: Any) -> int:
    now = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    print(now)
    return 0
