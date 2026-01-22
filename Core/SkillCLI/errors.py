"""Custom exceptions for SkillCLI.

The dispatcher and loader raise these exceptions to signal various
user-facing error conditions.  Separating them out makes it easy to
catch specific failure modes in the CLI and produce human-readable
messages without relying on broad ``Exception`` handling.
"""

from __future__ import annotations


class SkillCLIError(Exception):
    """Base class for all SkillCLI-related errors."""

    pass


class SkillNotFound(SkillCLIError):
    """Raised when a requested skill name does not exist in the registry."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Skill not found: {name}")
        self.name = name


class InvalidSkill(SkillCLIError):
    """Raised when a skill module is missing required exports or malformed."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Invalid skill at {path}: {reason}")
        self.path = path
        self.reason = reason


class DuplicateSkillError(SkillCLIError):
    """Raised when two skills declare the same canonical name."""

    def __init__(self, name: str, paths: list[str]) -> None:
        super().__init__(f"Duplicate skill name '{name}' declared by: {', '.join(paths)}")
        self.name = name
        self.paths = paths
