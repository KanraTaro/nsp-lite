"""Compatibility entrypoint for the NSPL skill surface.

The implementation now lives in :mod:`Core.NSPL.Entry.Surfaces.skill_surface`
so Entry and the historical SkillCLI module invocation share the same behavior.
"""

from __future__ import annotations

from Core.NSPL.Entry.Surfaces.skill_surface import (
    _build_top_parser,
    _dispatch_skill,
    _get_skills_root,
    _print_skill_listing,
    main,
)

__all__: list[str] = [
    "main",
    "_get_skills_root",
    "_build_top_parser",
    "_print_skill_listing",
    "_dispatch_skill",
]


if __name__ == "__main__":
    main()
