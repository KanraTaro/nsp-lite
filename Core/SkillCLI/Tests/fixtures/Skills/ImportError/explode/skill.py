"""A skill that raises an exception immediately on import.

This file is intentionally broken to verify that SkillCLI's
discovery and listing mechanisms do not import arbitrary skill modules.
Attempting to import this module should raise a RuntimeError.
"""

raise RuntimeError("This skill should not be imported during discovery")


def build_parser(parser):  # pragma: no cover
    pass


def run(args, ctx):  # pragma: no cover
    return 1
