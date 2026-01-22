"""Skill discovery and loading utilities for SkillCLI.

This module centralizes the logic for locating skill packages on disk,
parsing their metadata and importing their executable modules.  It is
deliberately kept free of any CLI concerns so that it can be unit
tested independently of argument parsing and user interaction.

Functions exported here must not write to disk and should only read
through NodeCTX where JSON parsing is required.  All exceptions raised
are defined in :mod:`Core.SkillCLI.errors` to make handling in the CLI
predictable.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# Always import NodeCTX relative to the Core package.  The Core
# package itself is available on sys.path by virtue of running tests
# from the repository root, so no bootstrap is necessary here.
from Core.NodeCTX import read_json

from .errors import DuplicateSkillError, InvalidSkill, SkillNotFound


def _discover_skill_json_files(skills_dir: Path) -> Iterable[Path]:
    """Yield all ``skill.json`` files under ``skills_dir`` recursively.

    Parameters
    ----------
    skills_dir: Path
        Root directory under which to search for skill packages.  This
        function does not verify that ``skills_dir`` exists; callers
        should handle missing roots as they see fit.

    Yields
    ------
    Path
        Paths to discovered ``skill.json`` files.  Files are yielded in
        sorted order for stable listing output.
    """
    if not skills_dir.exists():
        return []
    # Use rglob to find all skill.json files under any depth
    files = sorted(skills_dir.rglob("skill.json"))
    for json_path in files:
        yield json_path


def discover_skills(skills_dir: Path) -> Dict[str, Dict[str, object]]:
    """Discover skills under ``skills_dir`` using ``skill.json`` metadata.

    This function scans for ``skill.json`` files, parses them via
    NodeCTX.read_json and validates the required fields.  The result
    maps each canonical skill name to a dictionary containing the
    metadata and the absolute path to the entry file.

    Parameters
    ----------
    skills_dir: Path
        Root of the ``Skills`` directory tree.

    Returns
    -------
    dict[str, dict]
        Mapping from skill name to a descriptor with keys:
        ``meta`` (dict), ``entry_path`` (:class:`pathlib.Path`),
        ``skill_dir`` (:class:`pathlib.Path`).

    Raises
    ------
    InvalidSkill
        If a ``skill.json`` file is missing required fields or refers
        to an entry module that does not exist.
    DuplicateSkillError
        If two distinct skill packages declare the same name.
    """
    registry: Dict[str, Dict[str, object]] = {}
    duplicate_names: Dict[str, List[str]] = {}

    for json_path in _discover_skill_json_files(skills_dir):
        # Treat empty / placeholder skill.json as "not active yet"
        try:
            if json_path.stat().st_size == 0:
                # 0-byte placeholder
                continue

            raw_text: str = json_path.read_text(encoding="utf-8", errors="replace")
            if not raw_text.strip():
                # whitespace-only placeholder
                continue

            meta = read_json(json_path)
            if not isinstance(meta, dict):
                continue

        except Exception:
            # Broken or half-written JSON should not brick discovery.
            # We skip it and allow other valid skills to be discovered.
            continue

        # Validate required fields
        name = meta.get("name")
        version = meta.get("version")
        description = meta.get("description")
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(version, str) or not version.strip():
            continue
        if not isinstance(description, str) or not description.strip():
            continue

        # Determine entry file path; default to skill.py
        entry_name = meta.get("entry", "skill.py")
        skill_dir = json_path.parent
        entry_path = (skill_dir / entry_name).resolve()

        if not entry_path.is_file():
            continue

        # Check duplicate names
        if name in registry:
            duplicate_names.setdefault(name, [str(registry[name]["entry_path"])]).append(str(entry_path))
            continue

        registry[name] = {
            "meta": meta,
            "entry_path": entry_path,
            "skill_dir": skill_dir,
        }

    # If duplicates found, raise error summarising them
    if duplicate_names:
        # Use the first duplicate entry for error message; include all paths
        for dup_name, paths in duplicate_names.items():
            raise DuplicateSkillError(dup_name, paths)

    return registry


def load_skill_module(entry_path: Path) -> object:
    """Import a skill module from a specific file path.

    The module is loaded using ``importlib.util.spec_from_file_location``
    to avoid modifying ``sys.path`` globally.  It is assigned a unique
    name to avoid collisions in ``sys.modules``.  After loading, the
    module is validated to ensure it exposes the expected API.

    Parameters
    ----------
    entry_path: Path
        Absolute path to the ``skill.py`` module to load.

    Returns
    -------
    module
        The imported skill module.

    Raises
    ------
    InvalidSkill
        If the module is missing required exports or fails validation.
    """
    entry_path = Path(entry_path).resolve()
    if not entry_path.is_file():
        raise InvalidSkill(str(entry_path), "entry file does not exist")

    # Compute a unique module name based on the file path.  We avoid
    # leaking user-provided names into sys.modules to mitigate module
    # collision risk.
    module_name = f"_skillcli_module_{abs(hash(entry_path))}"

    spec = importlib.util.spec_from_file_location(module_name, str(entry_path))
    if spec is None or spec.loader is None:
        raise InvalidSkill(str(entry_path), "could not create import spec")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[call-arg]
    except Exception as e:
        # Surface import errors as InvalidSkill for nicer CLI messages
        raise InvalidSkill(str(entry_path), f"failed to import module: {e}") from e

    # Validate required exports
    if not hasattr(module, "build_parser") or not callable(getattr(module, "build_parser")):
        raise InvalidSkill(str(entry_path), "missing or non-callable 'build_parser' function")
    if not hasattr(module, "run") or not callable(getattr(module, "run")):
        raise InvalidSkill(str(entry_path), "missing or non-callable 'run' function")
    # SKILL_META is optional but when present should be a dict
    meta = getattr(module, "SKILL_META", None)
    if meta is not None and not isinstance(meta, dict):
        raise InvalidSkill(str(entry_path), "SKILL_META must be a dict when defined")

    return module


def resolve_skill(name: str, skills_dir: Path) -> Tuple[Dict[str, object], object]:
    """Resolve a skill by name and import its module.

    This helper combines discovery and loading.  It first scans for
    available skills under ``skills_dir`` and then imports the selected
    module by path.  If the name does not exist the ``SkillNotFound``
    exception is raised.

    Parameters
    ----------
    name: str
        Canonical name of the skill to load.
    skills_dir: Path
        Root of the skills tree to search within.

    Returns
    -------
    tuple
        A pair of (descriptor, module) where ``descriptor`` is the
        dictionary returned from :func:`discover_skills` for the skill
        and ``module`` is the imported Python module.
    """
    registry = discover_skills(skills_dir)
    if name not in registry:
        raise SkillNotFound(name)
    descriptor = registry[name]
    module = load_skill_module(descriptor["entry_path"])
    return descriptor, module
