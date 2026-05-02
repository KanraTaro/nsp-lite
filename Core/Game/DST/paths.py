"""RohBridge DST path discovery helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


SNAPSHOT_FILENAME = "roh_dst_snapshot.json"
COMMAND_FILENAME = "roh_dst_command.json"


@dataclass(frozen=True)
class DSTPathOverrides:
    snapshot_path: str | None = None
    command_path: str | None = None
    save_dir: str | None = None
    search_roots: tuple[str, ...] = ()


@dataclass(frozen=True)
class RohBridgePaths:
    snapshot_path: Path
    command_path: Path
    save_dir: Path
    source: str
    snapshot_mtime: float


def _expand_path(path: str) -> Path:
    return Path(path).expanduser()


def _snapshot_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _read_json_object_tolerant(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None

    start_index = raw.find("{")
    if start_index < 0:
        return None

    try:
        parsed = json.loads(raw[start_index:])
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed


def likely_dst_save_roots() -> list[Path]:
    roots = [
        Path("~/.klei/DoNotStarveTogether").expanduser(),
        Path("~/.local/share/Klei/DoNotStarveTogether").expanduser(),
    ]

    if os.name == "nt":
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            roots.append(Path(userprofile) / "Documents" / "Klei" / "DoNotStarveTogether")

    return roots


def is_valid_rohbridge_snapshot(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False

    snapshot = _read_json_object_tolerant(path)
    if snapshot is None:
        return False

    if snapshot.get("source") == "RohBridge":
        return True

    if "schema_version" in snapshot:
        return any(key in snapshot for key in ("world", "players", "side"))

    return False


def _unique_roots(search_roots: Sequence[str]) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()

    for raw_root in list(search_roots) + [str(path) for path in likely_dst_save_roots()]:
        if not raw_root:
            continue

        root = _expand_path(raw_root)
        key = str(root)
        if key in seen:
            continue

        seen.add(key)
        roots.append(root)

    return roots


def discover_rohbridge_snapshots(search_roots: Sequence[str] = ()) -> list[Path]:
    candidates: list[Path] = []

    for root in _unique_roots(search_roots):
        if not root.exists() or not root.is_dir():
            continue

        try:
            paths = root.rglob(SNAPSHOT_FILENAME)
        except OSError:
            continue

        for path in paths:
            if is_valid_rohbridge_snapshot(path):
                candidates.append(path)

    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates


def command_path_for_snapshot(snapshot_path: Path) -> Path:
    return snapshot_path.expanduser().parent / COMMAND_FILENAME


def _paths_from_save_dir(save_dir: str, source: str, command_path: str | None = None) -> RohBridgePaths:
    save_path = _expand_path(save_dir)
    snapshot_path = save_path / SNAPSHOT_FILENAME
    resolved_command_path = _expand_path(command_path) if command_path else save_path / COMMAND_FILENAME
    return RohBridgePaths(
        snapshot_path=snapshot_path,
        command_path=resolved_command_path,
        save_dir=save_path,
        source=source,
        snapshot_mtime=_snapshot_mtime(snapshot_path),
    )


def _paths_from_snapshot(
    snapshot_path: str,
    source: str,
    command_path: str | None = None,
) -> RohBridgePaths:
    snapshot = _expand_path(snapshot_path)
    resolved_command_path = _expand_path(command_path) if command_path else command_path_for_snapshot(snapshot)
    return RohBridgePaths(
        snapshot_path=snapshot,
        command_path=resolved_command_path,
        save_dir=snapshot.parent,
        source=source,
        snapshot_mtime=_snapshot_mtime(snapshot),
    )


def _paths_from_command(command_path: str, source: str) -> RohBridgePaths:
    command = _expand_path(command_path)
    snapshot = command.parent / SNAPSHOT_FILENAME
    return RohBridgePaths(
        snapshot_path=snapshot,
        command_path=command,
        save_dir=command.parent,
        source=source,
        snapshot_mtime=_snapshot_mtime(snapshot),
    )


def _env_search_roots() -> tuple[str, ...]:
    raw = os.environ.get("ROH_DST_SEARCH_ROOTS", "")
    if raw == "":
        return ()
    return tuple(part for part in raw.split(os.pathsep) if part)


def resolve_rohbridge_paths(overrides: DSTPathOverrides | None = None) -> RohBridgePaths:
    overrides = overrides or DSTPathOverrides()

    if overrides.snapshot_path:
        return _paths_from_snapshot(overrides.snapshot_path, "override:snapshot_path", overrides.command_path)

    if overrides.command_path:
        return _paths_from_command(overrides.command_path, "override:command_path")

    if overrides.save_dir:
        return _paths_from_save_dir(overrides.save_dir, "override:save_dir")

    env_snapshot_path = os.environ.get("ROH_DST_SNAPSHOT_PATH")
    env_command_path = os.environ.get("ROH_DST_COMMAND_PATH")
    env_save_dir = os.environ.get("ROH_DST_SAVE_DIR")

    if env_snapshot_path:
        return _paths_from_snapshot(env_snapshot_path, "env:ROH_DST_SNAPSHOT_PATH", env_command_path)

    if env_command_path:
        return _paths_from_command(env_command_path, "env:ROH_DST_COMMAND_PATH")

    if env_save_dir:
        return _paths_from_save_dir(env_save_dir, "env:ROH_DST_SAVE_DIR")

    search_roots = overrides.search_roots or _env_search_roots()
    snapshots = discover_rohbridge_snapshots(search_roots)
    if not snapshots:
        roots = _unique_roots(search_roots)
        root_list = ", ".join(str(root) for root in roots) or "(none)"
        raise FileNotFoundError(f"No valid RohBridge DST snapshot found under: {root_list}")

    snapshot_path = snapshots[0]
    return _paths_from_snapshot(str(snapshot_path), "discovery")


def resolve_snapshot_path(path: str | None = None) -> Path:
    if path:
        return _expand_path(path)
    return resolve_rohbridge_paths().snapshot_path


def resolve_command_path(path: str | None = None) -> Path:
    if path:
        return _expand_path(path)
    return resolve_rohbridge_paths().command_path
