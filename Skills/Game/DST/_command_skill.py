"""Shared helpers for thin DST command-writing skills."""

from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict

from Core.Game.DST.commands import (
    append_command_to_queue,
    attach_command_id,
    wait_for_command_result,
    write_command_legacy,
)
from Core.Game.DST.paths import (
    command_queue_path_for_command,
    command_result_path_for_command,
    resolve_rohbridge_paths,
)


def add_hidden_path_arg(parser: Any, help_text: Any = argparse.SUPPRESS) -> None:
    parser.add_argument(
        "--path",
        dest="path",
        default=None,
        help=help_text,
    )


def add_transport_args(parser: Any, path_help: Any = argparse.SUPPRESS) -> None:
    add_hidden_path_arg(parser, path_help)
    parser.add_argument(
        "--queue",
        dest="queue",
        action="store_true",
        help="Append to roh_dst_command_queue.json instead of writing the legacy command slot",
    )
    parser.add_argument(
        "--wait-result",
        dest="wait_result",
        action="store_true",
        help="Wait for roh_dst_command_result.json to acknowledge this command_id",
    )
    parser.add_argument(
        "--result-timeout",
        dest="result_timeout",
        type=float,
        default=3.0,
        help="Seconds to wait for a matching RohBridge command result",
    )
    parser.add_argument(
        "--result-interval",
        dest="result_interval",
        type=float,
        default=0.1,
        help="Seconds between command result polls",
    )
    parser.add_argument(
        "--command-id",
        dest="command_id",
        default=None,
        help="Optional command_id to attach before writing",
    )
    parser.add_argument("--queue-path", dest="queue_path", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--result-path", dest="result_path", default=None, help=argparse.SUPPRESS)


def _transport_paths(args: Any) -> tuple[Path, Path, Path]:
    explicit_path = getattr(args, "path", None)
    explicit_queue_path = getattr(args, "queue_path", None)
    explicit_result_path = getattr(args, "result_path", None)

    if explicit_path:
        command_path = Path(explicit_path).expanduser()
        queue_path = Path(explicit_queue_path).expanduser() if explicit_queue_path else command_queue_path_for_command(command_path)
        result_path = Path(explicit_result_path).expanduser() if explicit_result_path else command_result_path_for_command(command_path)
        return command_path, queue_path, result_path

    paths = resolve_rohbridge_paths()
    command_path = paths.command_path
    queue_path = Path(explicit_queue_path).expanduser() if explicit_queue_path else paths.command_queue_path
    result_path = Path(explicit_result_path).expanduser() if explicit_result_path else paths.command_result_path
    return command_path, queue_path, result_path


def write_command_payload(args: Any, ctx: Any, payload: Dict[str, Any]) -> int:
    path = str(Path(getattr(args, "path", "") or "roh_dst_command.json").expanduser())

    try:
        command_path, queue_path, result_path = _transport_paths(args)
        use_queue = bool(getattr(args, "queue", False))
        wait_result = bool(getattr(args, "wait_result", False))
        command = attach_command_id(payload, getattr(args, "command_id", None)) if (use_queue or wait_result or getattr(args, "command_id", None)) else dict(payload)

        if use_queue:
            write_result = append_command_to_queue(command, queue_path)
            path = str(queue_path)
        else:
            write_result = write_command_legacy(command, command_path)
            path = str(command_path)

        result = {
            "ok": True,
            "queued": use_queue,
            "path": str(Path(write_result["path"]).expanduser()),
            "command": command,
        }

        if "command_id" in command:
            result["command_id"] = command["command_id"]

        if wait_result:
            command_id = str(command["command_id"])
            try:
                bridge_result = wait_for_command_result(
                    command_id,
                    result_path,
                    float(getattr(args, "result_timeout", 3.0)),
                    float(getattr(args, "result_interval", 0.1)),
                )
                result["ok"] = bool(bridge_result.get("ok", False))
                result["result_path"] = str(result_path.expanduser())
                result["bridge_result"] = bridge_result
            except TimeoutError as exc:
                result["ok"] = False
                result["reason"] = "result_timeout"
                result["error"] = str(exc)
                result["result_path"] = str(result_path.expanduser())

        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0

    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "path": str(Path(path).expanduser()),
        }

        if getattr(ctx, "json", False):
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)

        return 1
