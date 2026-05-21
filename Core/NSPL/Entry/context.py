from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EntryContext:
    """Bootstrap context provided by the root ``nspl.py`` gateway."""

    repo_root: Path
    caller_cwd: Path

    @classmethod
    def from_paths(cls, repo_root: Path, caller_cwd: Path) -> "EntryContext":
        return cls(repo_root=Path(repo_root).resolve(), caller_cwd=Path(caller_cwd).resolve())
