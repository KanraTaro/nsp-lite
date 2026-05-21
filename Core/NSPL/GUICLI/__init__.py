from __future__ import annotations

__all__: list[str] = ["main"]


def __getattr__(name: str):
    if name == "main":
        from Core.NSPL.Entry.Surfaces.gui_surface import main

        return main
    raise AttributeError(name)
