"""Compatibility entrypoint for the NSPL GUI surface.

The implementation now lives in :mod:`Core.NSPL.Entry.Surfaces.gui_surface`
so Entry and the historical GUICLI module invocation share the same behavior.
"""

from __future__ import annotations

from Core.NSPL.Entry.Surfaces.gui_surface import (
    _build_top_parser,
    _dispatch_gui,
    _get_gui_root,
    _print_gui_listing,
    main,
)

__all__: list[str] = [
    "main",
    "_get_gui_root",
    "_build_top_parser",
    "_print_gui_listing",
    "_dispatch_gui",
]


if __name__ == "__main__":
    main()
