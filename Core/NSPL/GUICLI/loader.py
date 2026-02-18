from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from Core.NSPL.NodeCTX import read_json

from .errors import DuplicateGUIError, GUINotFound, InvalidGUI


def _discover_gui_json_files(gui_dir: Path) -> Iterable[Path]:
    if not gui_dir.exists():
        return []
    files = sorted(gui_dir.rglob("gui.json"))
    for json_path in files:
        yield json_path


def discover_guis(gui_dir: Path) -> Dict[str, Dict[str, object]]:
    registry: Dict[str, Dict[str, object]] = {}
    duplicate_names: Dict[str, List[str]] = {}

    for json_path in _discover_gui_json_files(gui_dir):
        try:
            if json_path.stat().st_size == 0:
                continue

            raw_text: str = json_path.read_text(encoding="utf-8", errors="replace")
            if not raw_text.strip():
                continue

            meta = read_json(json_path)
            if not isinstance(meta, dict):
                continue
        except Exception:
            continue

        name = meta.get("name")
        version = meta.get("version")
        description = meta.get("description")

        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(version, str) or not version.strip():
            continue
        if not isinstance(description, str) or not description.strip():
            continue

        entry_name = meta.get("entry", "launch.py")
        gui_pkg_dir = json_path.parent
        entry_path = (gui_pkg_dir / str(entry_name)).resolve()

        if not entry_path.is_file():
            continue

        if name in registry:
            duplicate_names.setdefault(name, [str(registry[name]["entry_path"])]).append(str(entry_path))
            continue

        registry[name] = {
            "meta": meta,
            "entry_path": entry_path,
            "gui_dir": gui_pkg_dir,
        }

    if duplicate_names:
        for dup_name, paths in duplicate_names.items():
            raise DuplicateGUIError(dup_name, paths)

    return registry


def load_gui_module(entry_path: Path) -> object:
    entry_path = Path(entry_path).resolve()
    if not entry_path.is_file():
        raise InvalidGUI(str(entry_path), "entry file does not exist")

    module_name = f"_guicli_module_{abs(hash(entry_path))}"
    spec = importlib.util.spec_from_file_location(module_name, str(entry_path))
    if spec is None or spec.loader is None:
        raise InvalidGUI(str(entry_path), "could not create import spec")

    module = importlib.util.module_from_spec(spec)

    # ✅ critical: register before exec_module so dataclasses can find the module
    import sys
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)  # type: ignore[call-arg]
    except Exception as e:
        raise InvalidGUI(str(entry_path), f"failed to import module: {e}") from e

    if not hasattr(module, "main") or not callable(getattr(module, "main")):
        raise InvalidGUI(str(entry_path), "missing or non-callable 'main(argv=None)' function")

    return module


def resolve_gui(name: str, gui_dir: Path) -> Tuple[Dict[str, object], object]:
    registry = discover_guis(gui_dir)
    if name not in registry:
        raise GUINotFound(name)
    descriptor = registry[name]
    module = load_gui_module(descriptor["entry_path"])
    return descriptor, module

