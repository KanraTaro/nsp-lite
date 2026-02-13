"""Atomic claim helper for ChatOps tasks.

The claim operation moves a task file from the Inbox to the Claimed
directory atomically.  In a concurrent environment with multiple workers,
only one worker should succeed in claiming a particular task. 
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def claim_task(task_path: Path, claimed_dir: Path, *, node_ctx) -> Optional[Path]:
    """Atomically move task_path into claimed_dir and return the new path.

    Uses NodeCTX so directory creation + atomic rename rules are centralized.
    """
    try:
        node_ctx.ensure_dir(claimed_dir)
        dest = claimed_dir / task_path.name
        node_ctx.atomic_replace(task_path, dest)
        return dest
    except FileNotFoundError:
        # The file no longer exists (claimed by another worker)
        return None
    except Exception as ex:
        try:
            # Leave a breadcrumb in the claimed dir so it’s visible without logs.
            node_ctx.ensure_dir(claimed_dir)
            marker = claimed_dir / f"{task_path.name}.claim_failed.txt"
            node_ctx.write_text_atomic(marker, f"claim_failed: {ex.__class__.__name__}: {ex}\n")
        except Exception:
            pass
        return None

