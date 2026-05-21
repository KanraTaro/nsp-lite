from __future__ import annotations


class EntryError(Exception):
    """Base class for Entry-level errors."""


class UnknownSurfaceError(EntryError):
    def __init__(self, surface: str) -> None:
        super().__init__(f"Unknown NSPL surface: {surface}")
        self.surface = surface
