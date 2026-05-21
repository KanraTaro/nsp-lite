from __future__ import annotations

import argparse
import os
from typing import Any


def build_parser(parser: argparse.ArgumentParser) -> None:
    return None


def run(args: argparse.Namespace, ctx: Any) -> int:
    print(os.environ.get("NSPL_CALLER_CWD", ""))
    return 0
