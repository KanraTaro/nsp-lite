from __future__ import annotations


class GUICLIError(Exception):
    pass


class GUINotFound(GUICLIError):
    def __init__(self, name: str) -> None:
        super().__init__(f"GUI not found: {name}")
        self.name = name


class InvalidGUI(GUICLIError):
    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Invalid GUI at {path}: {reason}")
        self.path = path
        self.reason = reason


class DuplicateGUIError(GUICLIError):
    def __init__(self, name: str, paths: list[str]) -> None:
        super().__init__(f"Duplicate GUI name '{name}' declared by: {', '.join(paths)}")
        self.name = name
        self.paths = paths

