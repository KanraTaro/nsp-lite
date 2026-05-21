"""SkillCLI package initializer.

SkillCLI remains importable for compatibility.  The command implementation now
lives under ``Core.NSPL.Entry.Surfaces.skill_surface`` and is exposed here as a
lazy ``main`` attribute to avoid circular imports while Entry imports SkillCLI
helper modules.
"""

from Core.NSPL.SkillCLI.runtime import SkillContext, create_ctx

__all__: list[str] = [
    "main",
    "SkillContext",
    "create_ctx",
]


def __getattr__(name: str):
    if name == "main":
        from Core.NSPL.Entry.Surfaces.skill_surface import main

        return main
    raise AttributeError(name)
