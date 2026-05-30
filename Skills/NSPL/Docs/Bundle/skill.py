from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from Core.NSPL.Docs import BundleError, generate_all, generate_auto_bundle, generate_bundle, generate_default, list_bundles


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--list", action="store_true", help="List configured bundles or report auto mode availability")
    parser.add_argument("--bundle", default=None, help="Generate one configured bundle by name")
    parser.add_argument("--all", action="store_true", help="Generate all manifest bundles, or the auto bundle without a manifest")
    parser.add_argument("--target", default=None, help="Target project folder (default: NSPL_CALLER_CWD or current cwd)")
    parser.add_argument("--auto", action="store_true", help="Ignore manifest and auto-bundle Markdown docs")
    parser.add_argument("--output-name", default=None, help="Output filename for the selected/default bundle")


def run(args: argparse.Namespace, ctx: Any) -> int:
    try:
        if args.list:
            payload = list_bundles(args.target)
            _print_list(payload, json_output=ctx.json)
            return 0

        if args.auto:
            result = generate_auto_bundle(args.target, output_name=args.output_name)
            _print_results([result.to_dict()], json_output=ctx.json)
            return 0

        if args.all:
            results = generate_all(args.target)
            _print_results([result.to_dict() for result in results], json_output=ctx.json)
            return 0

        if args.bundle:
            result = generate_bundle(args.bundle, args.target, output_name=args.output_name)
            _print_results([result.to_dict()], json_output=ctx.json)
            return 0

        result = generate_default(args.target, output_name=args.output_name)
        _print_results([result.to_dict()], json_output=ctx.json)
        return 0
    except BundleError as exc:
        if ctx.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True, separators=(",", ":")))
        else:
            print(f"Docs.Bundle error: {exc}", file=sys.stderr)
        return 1


def _print_list(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return

    if payload.get("manifest"):
        print(f"Target: {payload['target']}")
        print(f"Manifest: {payload['manifest']}")
        print(f"Default: {payload.get('default')}")
        print("Bundles:")
        for bundle in payload.get("bundles", []):
            marker = " (default)" if bundle.get("default") else ""
            description = bundle.get("description") or ""
            print(f"- {bundle['name']}{marker}: {description}")
        return

    print(f"Target: {payload['target']}")
    print("Manifest: none")
    print("Auto mode is available; running without flags will generate Bundles/PROJECT_CONTEXT.md.")


def _print_results(results: list[dict[str, Any]], *, json_output: bool) -> None:
    payload: Any = results[0] if len(results) == 1 else {"results": results}
    if json_output:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return

    for result in results:
        print(f"Generated {result['bundle']} -> {result['output']}")
        print(f"Sources: {len(result['sources'])}")
