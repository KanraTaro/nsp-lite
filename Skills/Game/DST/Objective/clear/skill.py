"""Game.DST.Objective.clear skill."""

from __future__ import annotations

import argparse
from typing import Any

from Core.Game.DST.commands import build_clear_objective_command
from Skills.Game.DST._command_skill import add_transport_args, write_command_payload


def build_parser(parser: argparse.ArgumentParser) -> None:
    add_transport_args(parser)


def run(args: argparse.Namespace, ctx: Any) -> int:
    payload = build_clear_objective_command()
    return write_command_payload(args, ctx, payload)
