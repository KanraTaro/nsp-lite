from __future__ import annotations

from pathlib import Path
from typing import Dict, Any


def _write_result(node_ctx, result_dir: Path, result_basename: str, result: Dict[str, Any]) -> Path:
    """Internal helper to write a result JSON using NodeCTX.

    The result file is named ``<result_basename>.result.json``.
    """
    node_ctx.ensure_dir(result_dir)
    result_path = result_dir / f"{result_basename}.result.json"
    node_ctx.write_json_atomic(result_path, result)
    return result_path


def complete_task(node_ctx, claimed_path: Path, done_dir: Path, result: Dict[str, Any]) -> Path:
    """Finalize a task successfully."""
    result_basename = claimed_path.stem  # pairs visually with the task file
    result_path = _write_result(node_ctx, done_dir, result_basename, result)

    try:
        node_ctx.ensure_dir(done_dir)
        node_ctx.atomic_replace(claimed_path, done_dir / claimed_path.name)
    except Exception as ex:
        # Don't fail silently. Leave a breadcrumb next to the result.
        try:
            marker = done_dir / f"{result_basename}.move_failed.txt"
            node_ctx.write_text_atomic(marker, f"move_failed: {ex.__class__.__name__}: {ex}\n")
        except Exception:
            pass

    return result_path


def fail_task(node_ctx, claimed_path: Path, failed_dir: Path, result: Dict[str, Any]) -> Path:
    """Finalize a task unsuccessfully."""
    result_basename = claimed_path.stem
    result_path = _write_result(node_ctx, failed_dir, result_basename, result)

    try:
        node_ctx.ensure_dir(failed_dir)
        node_ctx.atomic_replace(claimed_path, failed_dir / claimed_path.name)
    except Exception as ex:
        try:
            marker = failed_dir / f"{result_basename}.move_failed.txt"
            node_ctx.write_text_atomic(marker, f"move_failed: {ex.__class__.__name__}: {ex}\n")
        except Exception:
            pass

    return result_path

