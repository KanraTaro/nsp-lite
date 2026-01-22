from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


def _write_result(node_ctx, result_dir: Path, result_basename: str, result: Dict[str, Any]) -> Path:
    """Internal helper to write a result JSON using NodeCTX.

    The result file is named ``<result_basename>.result.json``.
    """
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / f"{result_basename}.result.json"
    node_ctx.write_json_atomic(result_path, result)
    return result_path


def complete_task(node_ctx, claimed_path: Path, done_dir: Path, result: Dict[str, Any]) -> Path:
    """Finalize a task successfully."""
    result_basename = claimed_path.stem  # pairs visually with the task file
    result_path = _write_result(node_ctx, done_dir, result_basename, result)

    try:
        done_dir.mkdir(parents=True, exist_ok=True)
        os.replace(str(claimed_path), str(done_dir / claimed_path.name))
    except Exception:
        pass

    return result_path


def fail_task(node_ctx, claimed_path: Path, failed_dir: Path, result: Dict[str, Any]) -> Path:
    """Finalize a task unsuccessfully."""
    result_basename = claimed_path.stem
    result_path = _write_result(node_ctx, failed_dir, result_basename, result)

    try:
        failed_dir.mkdir(parents=True, exist_ok=True)
        os.replace(str(claimed_path), str(failed_dir / claimed_path.name))
    except Exception:
        pass

    return result_path

