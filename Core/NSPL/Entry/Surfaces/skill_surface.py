"""Entry-owned implementation for the NSPL skill surface.

This module preserves the current SkillCLI command grammar and behavior while
moving the implementation under Entry.  ``Core.NSPL.SkillCLI.skillcli`` remains
a compatibility entrypoint that delegates here.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional

from Core.NSPL.SkillCLI import ctx as ctx_module
from Core.NSPL.SkillCLI.errors import DuplicateSkillError, InvalidSkill, SkillCLIError, SkillNotFound
from Core.NSPL.SkillCLI.loader import discover_skills, resolve_skill


def _get_skills_root(default_root: Path) -> Path:
    override = os.environ.get("SKILLS_ROOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            return (default_root / path).resolve()
        return path
    return (default_root / "Skills").resolve()


def _build_top_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="SkillCLI",
        description="RohTalk SkillCLI dispatcher",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List available skills",
        description="Discover and list all skills without importing them",
    )
    list_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include metadata fields in the listing (may be slower)",
    )

    skill_parser = subparsers.add_parser(
        "skill",
        help="Run a specific skill",
        description="Invoke a skill by canonical name",
    )
    skill_parser.add_argument("name", help="Canonical name of the skill to run")

    return parser


def _print_skill_listing(registry: dict, detailed: bool = False) -> None:
    for name in sorted(registry.keys()):
        entry = registry[name]
        if detailed:
            meta = entry.get("meta", {})
            print(f"{name}\t{meta.get('version')}\t{meta.get('description')}")
        else:
            print(name)


def _dispatch_skill(name: str, args: List[str], skills_dir: Path) -> int:
    descriptor, module = resolve_skill(name, skills_dir)
    meta = descriptor.get("meta", {})

    skill_parser = argparse.ArgumentParser(
        prog=name,
        description=meta.get("description", None),
    )
    skill_parser.add_argument("--debug", action="store_true", help="Enable debug mode with full tracebacks")
    skill_parser.add_argument("--json", action="store_true", help="Request JSON-formatted output if supported")
    skill_parser.add_argument("--node", dest="node_tag", default=None, help="Override node identifier")
    skill_parser.add_argument("--instance", dest="instance_id", default=None, help="Override instance identifier")
    skill_parser.add_argument("--global", dest="global_scope", action="store_true", help="Operate in global scope")

    try:
        module.build_parser(skill_parser)
    except Exception as e:
        raise InvalidSkill(str(descriptor["entry_path"]), f"error building parser: {e}") from e

    parsed_args = skill_parser.parse_args(args)
    context = ctx_module.create_ctx(parsed_args)

    start_monotonic: float = time.monotonic()

    try:
        context.node_ctx.log_event(
            root=context.root,
            instance_id=context.instance_id,
            node_tag=context.node_tag,
            global_scope=context.global_scope,
            domain="SkillCLI",
            file_name="skillcli.jsonl",
            kind="skill_started",
            rotation=context.node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
            extra={
                "skill": str(name),
                "argv": list(args),
            },
        )
    except Exception:
        pass

    try:
        result = module.run(parsed_args, context)
        exit_code: int = int(result) if isinstance(result, int) else 0
        duration_ms: int = int((time.monotonic() - start_monotonic) * 1000.0)

        try:
            context.node_ctx.log_event(
                root=context.root,
                instance_id=context.instance_id,
                node_tag=context.node_tag,
                global_scope=context.global_scope,
                domain="SkillCLI",
                file_name="skillcli.jsonl",
                kind="skill_finished",
                rotation=context.node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
                extra={
                    "skill": str(name),
                    "exit_code": int(exit_code),
                    "duration_ms": int(duration_ms),
                },
            )
        except Exception:
            pass

        return exit_code
    except Exception as e:
        duration_ms: int = int((time.monotonic() - start_monotonic) * 1000.0)
        try:
            context.node_ctx.log_event(
                root=context.root,
                instance_id=context.instance_id,
                node_tag=context.node_tag,
                global_scope=context.global_scope,
                domain="SkillCLI",
                file_name="skillcli.jsonl",
                kind="skill_failed",
                rotation=context.node_ctx.JsonlRotationPolicy(max_bytes=256_000, keep=5),
                extra={
                    "skill": str(name),
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "duration_ms": int(duration_ms),
                },
            )
        except Exception:
            pass

        if getattr(parsed_args, "debug", False):
            traceback.print_exc()
            raise

        print(f"Error executing skill '{name}': {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    top_parser = _build_top_parser()

    if not argv:
        top_parser.print_help()
        return

    if argv[0] in {"-h", "--help"}:
        top_parser.print_help()
        return

    command = argv[0]

    from Core.NSPL.ProjectRoot import get_effective_root

    project_root = get_effective_root()
    skills_dir = _get_skills_root(project_root)

    try:
        if command == "list":
            list_parser = argparse.ArgumentParser(
                prog="SkillCLI list",
                description="Discover and list all skills without importing them",
            )
            list_parser.add_argument(
                "--detailed",
                action="store_true",
                help="Include metadata fields in the listing (may be slower)",
            )
            list_args = list_parser.parse_args(argv[1:])
            registry = discover_skills(skills_dir)
            _print_skill_listing(registry, detailed=getattr(list_args, "detailed", False))
            return

        if command == "skill":
            if len(argv) < 2:
                print("Error: missing skill name", file=sys.stderr)
                top_parser.print_usage()
                sys.exit(1)
            skill_name = argv[1]
            skill_args = argv[2:]
            exit_code = _dispatch_skill(skill_name, skill_args, skills_dir)
            sys.exit(exit_code)

        print(f"Unknown command: {command}", file=sys.stderr)
        top_parser.print_usage()
        sys.exit(1)
    except DuplicateSkillError as e:
        print(f"Duplicate skill name detected: {e}", file=sys.stderr)
        sys.exit(1)
    except SkillNotFound as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except InvalidSkill as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except SkillCLIError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
