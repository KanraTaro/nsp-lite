"""NSPL.Tools.Weather.get skill.

This is a simple proving skill for tool execution through SkillCLI.

It returns a fake weather payload for a requested city. The purpose of
this skill is not real weather lookup yet, but to provide a clean,
argument-taking, JSON-friendly SkillCLI tool for RohTalk integration
tests.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--city",
        dest="city",
        required=True,
        help="City name to fetch weather for",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    city = str(getattr(args, "city", "") or "").strip()

    result: Dict[str, Any] = {
        "city": city,
        "forecast": "Partly cloudy",
        "temp_f": 82,
    }

    if getattr(ctx, "json", False):
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    else:
        print(f"{city}: {result['forecast']}, {result['temp_f']}F")

    return 0
