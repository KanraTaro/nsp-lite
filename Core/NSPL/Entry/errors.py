from __future__ import annotations


class EntryError(Exception):
    """Base class for Entry-level errors."""


class UnknownSurfaceError(EntryError):
    def __init__(self, surface: str) -> None:
        super().__init__(f"Unknown NSPL surface: {surface}")
        self.surface = surface


class WebEntryError(EntryError):
    """Base class for Web Entry surface errors."""


class WebAppNotFound(WebEntryError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Web app not found: {name}")
        self.name = name


class InvalidWebApp(WebEntryError):
    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Invalid Web app at {path}: {reason}")
        self.path = path
        self.reason = reason


class DuplicateWebAppError(WebEntryError):
    def __init__(self, name: str, paths: list[str]) -> None:
        super().__init__(f"Duplicate Web app name '{name}' declared by: {', '.join(paths)}")
        self.name = name
        self.paths = paths
