"""Command-line interface implementation for SkillCLI.

This module parses arguments, delegates discovery and dispatch to the
loader and context helpers, and handles user-facing error messages.
It is the primary entry point for the ``skill`` and ``list`` subcommands
when invoked via ``python -m Core.SkillCLI`` or directly as a script.

Notes
-----
* All disk I/O, including reading ``skill.json``, happens through
  NodeCTX functions in :mod:`Core.SkillCLI.loader`.
* SkillCLI itself does not write to disk during normal operation.
* To override the location of the ``Skills`` tree, set the
  ``SKILLS_ROOT`` environment variable.  This is primarily intended
  for unit tests and should not be necessary for end-users.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path
from typing import List, Optional

from . import ctx as ctx_module
from .errors import SkillCLIError, SkillNotFound, InvalidSkill, DuplicateSkillError
from .loader import discover_skills, resolve_skill


def _get_skills_root(default_root: Path) -> Path:
    """Determine the directory under which skills live.

    SkillCLI looks for skills in a ``Skills`` folder relative to the
    repository root by default.  For testing or advanced usage the
    ``SKILLS_ROOT`` environment variable may override this directory
    entirely.  If the override is relative it is resolved against
    ``default_root``.
    """
    override = os.environ.get("SKILLS_ROOT")
    if override:
        path = Path(override)
        if not path.is_absolute():
            return (default_root / path).resolve()
        return path
    return (default_root / "Skills").resolve()


def _build_top_parser() -> argparse.ArgumentParser:
    """Create and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="SkillCLI",
        description="RohTalk SkillCLI dispatcher",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list subcommand
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

    # skill subcommand
    skill_parser = subparsers.add_parser(
        "skill",
        help="Run a specific skill",
        description="Invoke a skill by canonical name",
    )
    skill_parser.add_argument("name", help="Canonical name of the skill to run")
    # This parser will defer the rest of the arguments to the skill-specific parser later

    return parser


def _print_skill_listing(registry: dict, detailed: bool = False) -> None:
    """Print a human-readable list of discovered skills."""
    # Sort by canonical name for deterministic output
    for name in sorted(registry.keys()):
        entry = registry[name]
        if detailed:
            meta = entry.get("meta", {})
            # Show description and version in a tab-separated format
            print(f"{name}\t{meta.get('version')}\t{meta.get('description')}")
        else:
            print(name)


def _dispatch_skill(name: str, args: List[str], skills_dir: Path) -> int:
    """Load and run a skill, returning its exit code.

    Parameters
    ----------
    name: str
        The canonical name of the skill to execute.
    args: list[str]
        Remaining CLI arguments to pass to the skill's parser.
    skills_dir: Path
        Root of the skills tree.

    Returns
    -------
    int
        The exit code returned by the skill's ``run`` function or 0 on success.
    """
    # Resolve the skill descriptor and module
    descriptor, module = resolve_skill(name, skills_dir)
    meta = descriptor.get("meta", {})

    # Construct parser for this skill
    skill_parser = argparse.ArgumentParser(
        prog=name,
        description=meta.get("description", None),
    )
    # Standard flags available to every skill
    skill_parser.add_argument("--debug", action="store_true", help="Enable debug mode with full tracebacks")
    skill_parser.add_argument("--json", action="store_true", help="Request JSON-formatted output if supported")
    skill_parser.add_argument("--node", dest="node_tag", default=None, help="Override node identifier")
    skill_parser.add_argument("--instance", dest="instance_id", default=None, help="Override instance identifier")
    skill_parser.add_argument("--global", dest="global_scope", action="store_true", help="Operate in global scope")

    # Let the skill extend the parser with its own flags/positional args
    try:
        module.build_parser(skill_parser)
    except Exception as e:
        raise InvalidSkill(str(descriptor["entry_path"]), f"error building parser: {e}") from e

    # Parse the remaining arguments for the skill
    parsed_args = skill_parser.parse_args(args)

    # Build context object
    context = ctx_module.create_ctx(parsed_args)

    # Execute the skill and propagate its exit code
    try:
        result = module.run(parsed_args, context)
        # Normalize return to integer
        return int(result) if isinstance(result, int) else 0
    except Exception as e:
        # If debug flag is set, print full traceback and re-raise
        if getattr(parsed_args, "debug", False):
            traceback.print_exc()
            # Propagate underlying exception code if provided
            raise
        # Otherwise, print a concise error and return non-zero
        print(f"Error executing skill '{name}': {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the SkillCLI command-line interface.

    Manual top-level parsing is used here to avoid argparse consuming
    ``--help`` intended for individual skills.  Only the first token of
    ``argv`` is inspected to determine the command (``list`` or
    ``skill``).  Subsequent arguments are delegated to a command-
    specific parser or passed through to the target skill.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Build a top-level parser solely for producing usage/help messages
    top_parser = _build_top_parser()

    # No arguments - print help
    if not argv:
        top_parser.print_help()
        return

    # Global help requests
    if argv[0] in {"-h", "--help"}:
        top_parser.print_help()
        return

    command = argv[0]

    # Determine skills directory based on project root and environment
    from Core.ProjectRoot import get_effective_root
    project_root = get_effective_root()
    skills_dir = _get_skills_root(project_root)

    try:
        if command == "list":
            # Parse list-specific flags
            list_parser = argparse.ArgumentParser(
                prog="SkillCLI list",
                description="Discover and list all skills without importing them",
            )
            list_parser.add_argument(
                "--detailed",
                action="store_true",
                help="Include metadata fields in the listing (may be slower)",
            )
            try:
                list_args = list_parser.parse_args(argv[1:])
            except SystemExit:
                # Let argparse handle help/usage for the list subcommand
                raise
            registry = discover_skills(skills_dir)
            _print_skill_listing(registry, detailed=getattr(list_args, "detailed", False))
            return

        elif command == "skill":
            # Expect at least the skill name
            if len(argv) < 2:
                print("Error: missing skill name", file=sys.stderr)
                top_parser.print_usage()
                sys.exit(1)
            skill_name = argv[1]
            skill_args = argv[2:]
            exit_code = _dispatch_skill(skill_name, skill_args, skills_dir)
            sys.exit(exit_code)
        else:
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


if __name__ == "__main__":
    main()
