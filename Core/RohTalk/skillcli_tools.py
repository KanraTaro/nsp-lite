"""Programmatic SkillCLI execution helpers for RohTalk tools.

This module provides a bridge between RohTalk tool execution and
SkillCLI skills without spawning a subprocess.

Design intent:
- let RohTalk execute SkillCLI skills directly in-process
- preserve the canonical SkillCLI contract
- capture stdout/stderr for fallback parsing
- prefer structured JSON results when available
- keep subprocess execution as a future fallback only if needed
"""

from __future__ import annotations

import argparse
import json
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List

from Core.NSPL.SkillCLI.loader import resolve_skill

from .tool_naming import build_skill_tool_name_map, skill_name_to_tool_name


DST_DIRECTOR_QUEUED_RESULT_SKILLS = {
    "Game.DST.Announce.text",
    "Game.DST.Objective.collect",
    "Game.DST.Objective.clear",
    "Game.DST.Chaos.set_tier",
    "Game.DST.Chaos.spawn_supplies",
    "Game.DST.Chaos.spawn_enemy",
    "Game.DST.Chaos.trigger_event",
    "Game.DST.Chaos.clear_enemies",
    "Game.DST.Chaos.clear_bosses",
    "Game.DST.Objective.player_collect",
    "Game.DST.Objective.clear_player",
    "Game.DST.Objective.status",
}

DST_DIRECTOR_RESULT_TIMEOUT_SECONDS = 15.0
DST_DIRECTOR_RESULT_INTERVAL_SECONDS = 0.25


def _skills_root_from_ctx(ctx: Any) -> Path:
    """Resolve the Skills root from the current runtime context."""
    return (Path(ctx.root) / "Skills").resolve()


def _arg_name_to_flag(name: str) -> str:
    """Convert a dict key into a CLI flag name."""
    cleaned = str(name).strip()
    if cleaned == "":
        raise ValueError("Tool argument name cannot be empty.")
    return "--" + cleaned.replace("_", "-")


def _dict_to_argv(arguments: Dict[str, Any]) -> List[str]:
    """Convert tool-call arguments into SkillCLI-style argv.

    Supported rules:
    - bool True  -> --flag
    - bool False -> omitted
    - None       -> omitted
    - str/int/float -> --flag value
    - list/tuple -> repeated --flag value
    - dict       -> --flag <json-string>

    Positional-only skills are intentionally not supported in this
    first pass.
    """
    argv: List[str] = []

    for key, value in arguments.items():
        flag = _arg_name_to_flag(str(key))

        if value is None:
            continue

        if isinstance(value, bool):
            if value:
                argv.append(flag)
            continue

        if isinstance(value, (str, int, float)):
            argv.extend([flag, str(value)])
            continue

        if isinstance(value, (list, tuple)):
            for item in value:
                argv.extend([flag, str(item)])
            continue

        if isinstance(value, dict):
            argv.extend([flag, json.dumps(value, separators=(",", ":"), sort_keys=True)])
            continue

        argv.extend([flag, str(value)])

    return argv


def canonical_skill_name_to_tool_name(skill_name: str) -> str:
    """Expose the preferred model-facing tool name for a canonical skill name."""
    return skill_name_to_tool_name(skill_name)


def build_tool_name_map(skill_names: List[str]) -> Dict[str, str]:
    """Build model-facing tool name -> canonical skill name map."""
    return build_skill_tool_name_map(skill_names)


def execute_skill(ctx: Any, skill_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a SkillCLI skill directly and return a normalized result.

    Return shape:
    - parsed JSON object if stdout is valid JSON
    - otherwise a fallback object containing stdout/stderr/exit_code

    Raises:
        Exception if skill resolution, parsing, or execution fails in a
        way that should be surfaced to the caller.
    """
    skills_dir = _skills_root_from_ctx(ctx)
    descriptor, module = resolve_skill(skill_name, skills_dir)

    parser = argparse.ArgumentParser(
        prog=skill_name,
        description=descriptor.get("meta", {}).get("description", None),
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--json", action="store_true", help="Request JSON output if supported")
    parser.add_argument("--node", dest="node_tag", default=None, help="Override node identifier")
    parser.add_argument("--instance", dest="instance_id", default=None, help="Override instance identifier")
    parser.add_argument("--global", dest="global_scope", action="store_true", help="Operate in global scope")

    module.build_parser(parser)

    skill_arguments = dict(arguments)
    if skill_name in DST_DIRECTOR_QUEUED_RESULT_SKILLS:
        skill_arguments.setdefault("queue", True)
        skill_arguments.setdefault("wait_result", True)
        skill_arguments.setdefault("result_timeout", DST_DIRECTOR_RESULT_TIMEOUT_SECONDS)
        skill_arguments.setdefault("result_interval", DST_DIRECTOR_RESULT_INTERVAL_SECONDS)

    stdout_buffer = StringIO()
    stderr_buffer = StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        argv = ["--json"]
        argv.extend(_dict_to_argv(skill_arguments))

        try:
            parsed_args = parser.parse_args(argv)
        except SystemExit as exc:
            code = int(getattr(exc, "code", 2) or 2)
            raise RuntimeError(
                f"Skill '{skill_name}' argument parsing failed with exit_code={code}"
                + (f": {stderr_buffer.getvalue().strip()}" if stderr_buffer.getvalue().strip() else "")
            ) from exc

        exec_ctx = replace(
            ctx,
            debug=bool(getattr(parsed_args, "debug", False)),
            json=True,
        )

        result = module.run(parsed_args, exec_ctx)

    exit_code = int(result) if isinstance(result, int) else 0
    stdout_text = stdout_buffer.getvalue().strip()
    stderr_text = stderr_buffer.getvalue().strip()

    if exit_code != 0:
        raise RuntimeError(
            f"Skill '{skill_name}' failed with exit_code={exit_code}"
            + (f": {stderr_text}" if stderr_text else "")
        )

    if stdout_text != "":
        try:
            return json.loads(stdout_text)
        except Exception:
            pass

    return {
        "exit_code": exit_code,
        "stdout": stdout_text,
        "stderr": stderr_text,
    }
