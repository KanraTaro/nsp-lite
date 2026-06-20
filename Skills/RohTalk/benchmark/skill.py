"""RohTalk benchmark skill."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from Core.RohTalk.Benchmarks import (
    BenchmarkRequest,
    format_summary,
    run_benchmark,
    save_results,
)
from Core.RohTalk.Benchmarks.results import results_to_json
from Core.RohTalk.config import parse_model_option_args


MODES = [
    "no-tools",
    "tool-dry",
    "dst-director-dry",
    "dst-director-live",
]


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", dest="model", default=None, help="Optional model override")
    parser.add_argument("--model-profile", dest="model_profile", default=None, help="Optional model profile name")
    parser.add_argument("--host", dest="host", default=None, help="Optional backend URL override")
    parser.add_argument(
        "--model-option",
        dest="model_options",
        action="append",
        default=[],
        help="Model runtime option as key=value; repeatable",
    )
    parser.add_argument("--toolkit", dest="toolkit", default=None, help="Optional toolkit to expose when tools are enabled")
    tool_group = parser.add_mutually_exclusive_group()
    tool_group.add_argument("--tools", dest="tools_enabled", action="store_true", help="Enable tool-capable benchmark turns")
    tool_group.add_argument(
        "--no-tools",
        dest="tools_enabled",
        action="store_false",
        help="Disable tools even when a toolkit or tool mode is selected",
    )
    parser.set_defaults(tools_enabled=None)
    parser.add_argument("--mode", dest="mode", choices=MODES, default="no-tools", help="Benchmark mode")
    parser.add_argument("--suite", dest="suite", default="smoke", help="Benchmark suite")
    parser.add_argument("--case", dest="case_ids", action="append", default=[], help="Benchmark case id to run; repeatable")
    parser.add_argument("--iterations", dest="iterations", type=int, default=1, help="Number of iterations")
    parser.add_argument("--timeout", dest="timeout", type=float, default=180.0, help="Per-case model timeout in seconds")
    parser.add_argument("--save", dest="save", action="store_true", help="Append results to RohTalk benchmark JSONL logs")
    parser.add_argument(
        "--allow-live-dst-actions",
        dest="allow_live_dst_actions",
        action="store_true",
        help="Allow live DST-mutating benchmark actions",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    if int(args.iterations or 1) < 1:
        print("--iterations must be at least 1.", file=sys.stderr)
        return 2
    if float(args.timeout or 0.0) <= 0:
        print("--timeout must be greater than 0.", file=sys.stderr)
        return 2
    tools_enabled = getattr(args, "tools_enabled", None)
    if args.mode == "dst-director-live" and tools_enabled is not False and not bool(args.allow_live_dst_actions):
        print("dst-director-live requires --allow-live-dst-actions.", file=sys.stderr)
        return 2

    try:
        model_options = parse_model_option_args(getattr(args, "model_options", []))
        request = BenchmarkRequest(
            suite=str(args.suite),
            mode=str(args.mode),
            iterations=int(args.iterations),
            timeout_s=float(args.timeout),
            model=args.model,
            model_profile=args.model_profile,
            host=args.host,
            model_options=model_options if model_options else None,
            toolkit=args.toolkit,
            tools_enabled=tools_enabled,
            case_ids=list(getattr(args, "case_ids", []) or []) or None,
            allow_live_dst_actions=bool(args.allow_live_dst_actions),
        )
        results = run_benchmark(ctx, request)
        saved_paths = save_results(ctx, results) if bool(args.save) else None
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if bool(getattr(ctx, "json", False)):
        print(results_to_json(results, saved_paths=saved_paths))
    else:
        print(format_summary(results))
        if saved_paths is not None:
            print("Saved:")
            for label, path in saved_paths.items():
                print(f"  {label}: {path}")

    return 0
