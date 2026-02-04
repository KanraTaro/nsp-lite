"""
Project Root discovery utilities.

ProjectRoot provides a simple, configurable way to locate the root of a
project at runtime. It searches upward from a starting directory for a
file that marks the root. The search order and depth are governed by
environment variables documented in the module's docstring. When no
marker is found within the configured depth the starting directory is
returned and a warning is logged.

The module exposes two public functions:

``find_root(start_dir: Path, marker: str, anchors: list[str], max_depth: int)``
    Perform a bounded upward search for the first directory containing the
    marker file or any of the anchor files. Returns the matching
    directory as a :class:`pathlib.Path` or ``None`` if no match is found.

``get_effective_root(start_dir: Optional[Path] = None)``
    Convenience wrapper that populates sensible defaults from environment
    variables and returns a resolved :class:`pathlib.Path` to the
    discovered root. Falls back deterministically to the starting
    directory when no marker is found.

Neither function writes to disk; they only read the filesystem and
emit log messages. See the README for further details.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, List, Optional

logger = logging.getLogger("ProjectRoot.skill")

__nsp_module_name__ = "ProjectRoot"
__nsp_module_version__ = "1.0.0"


def _split_anchor_list(value: str) -> List[str]:
    """Split a comma-separated list of anchor filenames.

    Leading and trailing whitespace on each element is stripped. Empty
    strings are ignored.

    Parameters
    ----------
    value: str
        Raw comma-separated string from the environment.

    Returns
    -------
    list[str]
        Cleaned list of anchor filenames.
    """
    anchors: List[str] = []
    for part in value.split(","):
        cleaned = part.strip()
        if cleaned:
            anchors.append(cleaned)
    return anchors


def find_root(start_dir: Path, marker: str, anchors: Iterable[str], max_depth: int) -> Optional[Path]:
    """Search upward from ``start_dir`` for a project root.

    A directory qualifies as the project root if it contains either the
    marker file or any of the anchor files. The search stops when a
    qualifying directory is found, when ``max_depth`` parent directories
    have been inspected, or when the filesystem root is reached.

    Parameters
    ----------
    start_dir: Path
        The directory from which to begin the upward search. This
        directory will be resolved to its absolute form.
    marker: str
        Filename that explicitly declares a directory as the project root.
        If empty/whitespace, marker checks are effectively disabled.
    anchors: Iterable[str]
        One or more filenames that act as root anchors when ``marker`` is
        absent.
    max_depth: int
        Maximum number of parent directories to traverse before giving up.
        Negative values are treated as 0.

    Returns
    -------
    Optional[Path]
        The first directory containing the marker or an anchor. ``None``
        is returned if no qualifying directory is found within the
        allowed depth.
    """
    current = Path(start_dir).resolve()

    # Clamp max_depth for predictable behavior.
    safe_max_depth = max(0, int(max_depth))

    depth = 0
    marker_path = marker.strip() if marker is not None else ""
    anchor_files = list(anchors)

    logger.debug(
        "Starting root search from %s with marker %s, anchors %s, max_depth %d",
        current,
        marker_path,
        anchor_files,
        safe_max_depth,
    )

    while True:
        # Check for marker file (unless marker disabled by empty string)
        if marker_path and (current / marker_path).is_file():
            logger.info("Found root marker '%s' in %s", marker_path, current)
            return current

        # Check for any anchor files
        for anchor in anchor_files:
            if (current / anchor).is_file():
                logger.info("Found anchor file '%s' in %s", anchor, current)
                return current

        # Stop if we've searched the allowed depth or reached filesystem root
        if depth >= safe_max_depth or current.parent == current:
            break

        current = current.parent
        depth += 1

    logger.debug("No root found after checking %d directories; returning None", depth + 1)
    return None


def get_effective_root(start_dir: Optional[Path] = None) -> Path:
    """Resolve the effective project root using environment defaults.

    This function wraps :func:`find_root` and pulls configuration from
    environment variables. If a starting directory is not provided it
    uses the ``RR_START_DIR`` environment variable when available or
    falls back to the current working directory. The search is governed
    by the following variables:

    ``RR_ROOT_MARKER``
        Name of a file that explicitly marks a directory as the root.
        Defaults to ``.root``.

    ``RR_ANCHOR_FILES``
        Comma-separated list of files that act as root anchors when the
        marker file is absent. Defaults to ``kontainer.json``.

    ``RR_MAX_DEPTH``
        Maximum number of parent directories to ascend during the search.
        Defaults to ``25``. Negative values are treated as 0.

    ``RR_START_DIR``
        Optional. When set and no ``start_dir`` is passed, this
        directory is used as the starting point for the search. When
        neither is provided the current working directory is used.

    Returns
    -------
    Path
        The resolved path to the project root. When no marker or
        anchors are found within ``RR_MAX_DEPTH`` directories the
        starting directory is returned and a warning is logged.
    """
    # Absolute override: RR_ROOT wins when provided.
    env_root = os.environ.get("RR_ROOT")
    if env_root:
        forced_root = Path(env_root).expanduser().resolve()
        if forced_root.is_dir():
            return forced_root
        logger.warning("RR_ROOT is set but is not a directory: %s", forced_root)
    
    # Determine starting directory
    if start_dir is not None:
        base_dir = Path(start_dir).resolve()
    else:
        env_start = os.environ.get("RR_START_DIR")
        if env_start:
            base_dir = Path(env_start).resolve()
        else:
            base_dir = Path.cwd().resolve()

    # Read environment defaults with fallbacks
    marker = os.environ.get("RR_ROOT_MARKER", ".root")
    marker_clean = marker.strip() if marker is not None else ".root"

    anchor_env = os.environ.get("RR_ANCHOR_FILES", "kontainer.json")
    anchors = _split_anchor_list(anchor_env)

    try:
        parsed_depth = int(os.environ.get("RR_MAX_DEPTH", "25"))
    except ValueError:
        parsed_depth = 25

    max_depth = max(0, parsed_depth)

    logger.debug(
        "Effective root discovery starting at %s (marker=%s, anchors=%s, max_depth=%d)",
        base_dir,
        marker_clean,
        anchors,
        max_depth,
    )

    root = find_root(base_dir, marker_clean, anchors, max_depth)
    if root is None:
        logger.warning(
            "ProjectRoot fallback: no root marker or anchors found within %s levels from %s; using starting directory",
            max_depth,
            base_dir,
        )
        return base_dir

    return root

