# Core/SkillCLI/runtime.py
"""
Public convenience exports for SkillCLI.

This module is the "stable surface" other code can import from without
needing to know internal file boundaries.
"""

from __future__ import annotations

from Core.NSPL.SkillCLI.ctx import SkillContext, create_ctx
from Core.NSPL.SkillCLI.loader import discover_skills, load_skill_module, resolve_skill

__all__: list[str] = [
    "SkillContext",
    "create_ctx",
    "discover_skills",
    "load_skill_module",
    "resolve_skill",
]

