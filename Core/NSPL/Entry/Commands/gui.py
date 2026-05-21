from __future__ import annotations

from typing import List

from Core.NSPL.Entry.context import EntryContext


def _forward_to_module_main(module_main, argv: List[str]) -> int:
    result = module_main(argv)
    if isinstance(result, int):
        return int(result)
    return 0


def main(argv: List[str], context: EntryContext | None = None) -> int:
    del context
    from Core.NSPL.GUICLI.guicli import main as gui_main

    return _forward_to_module_main(gui_main, argv)
