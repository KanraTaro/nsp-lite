"""Atomic claim helper for ChatOps tasks.

The claim operation moves a task file from the Inbox to the Claimed
directory atomically.  In a concurrent environment with multiple workers,
only one worker should succeed in claiming a particular task.  The
lowest-level primitive used is ``os.replace``, which performs an atomic
rename within a single filesystem.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def claim_task(task_path: Path, claimed_dir: Path) -> Optional[Path]:
    """Atomically move ``task_path`` into ``claimed_dir`` and return the new path.

    If another worker has already claimed or removed the file, or if any
    exception occurs during the rename, ``None`` is returned.  On
    success, the returned path points to the file in the Claimed
    directory.  The caller should assume ownership of the file.

    Args:
        task_path: The full path to the task file in the Inbox.
        claimed_dir: The directory to move the task into.  It will be
            created if necessary.

    Returns:
        The new ``Path`` of the claimed file on success, or ``None`` on
        failure.
    """
    try:
        claimed_dir.mkdir(parents=True, exist_ok=True)
        dest = claimed_dir / task_path.name
        # os.replace performs an atomic rename, overwriting any existing
        # file at dest.  On POSIX filesystems this operation is atomic.
        os.replace(str(task_path), str(dest))
        return dest
    except FileNotFoundError:
        # The file no longer exists (claimed by another worker)
        return None
    except Exception:
        # Other errors (e.g. permission) should not crash the worker
        return None
