from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from Core.NSPL.Entry.errors import DuplicateWebAppError
from Core.NSPL.NodeCTX import read_json


def _discover_web_json_files(web_dir: Path) -> Iterable[Path]:
    if not web_dir.exists():
        return []
    files = sorted(web_dir.rglob("web.json"))
    for json_path in files:
        yield json_path


def discover_web_apps(web_dir: Path) -> Dict[str, Dict[str, object]]:
    registry: Dict[str, Dict[str, object]] = {}
    duplicate_names: Dict[str, List[str]] = {}

    for json_path in _discover_web_json_files(web_dir):
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

        entry_name = meta.get("entry", "app.py")
        factory_name = meta.get("factory", "create_app")
        web_app_dir = json_path.parent
        entry_path = (web_app_dir / str(entry_name)).resolve()

        if not entry_path.is_file():
            continue

        if name in registry:
            duplicate_names.setdefault(name, [str(registry[name]["entry_path"])]).append(str(entry_path))
            continue

        registry[name] = {
            "meta": meta,
            "entry_path": entry_path,
            "web_dir": web_app_dir,
            "factory": str(factory_name),
        }

    if duplicate_names:
        for dup_name, paths in duplicate_names.items():
            raise DuplicateWebAppError(dup_name, paths)

    return registry
