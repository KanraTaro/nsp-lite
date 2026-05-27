from __future__ import annotations

from typing import List

from Core.NSPL.Entry.context import EntryContext


def _forward_to_module_main(module_main, argv: List[str]) -> int:
    result = module_main(argv)
    if isinstance(result, int):
        return int(result)
    return 0


def _skillcli_argv_from_entry(argv: List[str]) -> List[str]:
    if not argv or argv[0] in {"list", "-h", "--help"}:
        return argv
    return ["skill", *argv]


def main(argv: List[str], context: EntryContext | None = None) -> int:
    del context
    from Core.NSPL.Entry.Surfaces.skill_surface import main as skill_main

    return _forward_to_module_main(skill_main, _skillcli_argv_from_entry(argv))
