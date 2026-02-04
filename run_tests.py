"""
run_tests.py

Repo-wide unittest runner.

Rules:
- Repo root is found by walking up until we see: .root file AND Core/ directory
- Adds repo root to sys.path so imports like "Core.*" work consistently
- Discovers tests ONLY inside:
    Core/**/Tests
    Skills/**/Tests  (when present)
- Pattern: test_*.py
"""

from __future__ import annotations

import sys
import unittest
import argparse
import os

from pathlib import Path
from typing import List


def _find_repo_root(start: Path) -> Path:
    p: Path = start.resolve()
    while p.parent != p:
        if (p / ".root").is_file() and (p / "Core").is_dir():
            return p
        p = p.parent
    raise ModuleNotFoundError("NSP repo root not found (missing .root + Core/)")


def _find_tests_dirs(repo_root: Path) -> List[Path]:
    tests_dirs: List[Path] = []

    core_root: Path = repo_root / "Core"
    if core_root.is_dir():
        # Only match ".../Tests" directories, not just any test_*.py anywhere.
        tests_dirs.extend([p for p in core_root.rglob("Tests") if p.is_dir()])

    skills_root: Path = repo_root / "Skills"
    if skills_root.is_dir():
        tests_dirs.extend([p for p in skills_root.rglob("Tests") if p.is_dir()])

    # Deterministic order helps when debugging CI logs later.
    tests_dirs_sorted: List[Path] = sorted(set(tests_dirs), key=lambda x: str(x))
    return tests_dirs_sorted


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_tests.py",
        add_help=True,
        description="Repo-wide unittest runner.",
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="Enable live Ollama integration test (sets NSPL_RUN_OLLAMA_INTEGRATION=1 and default model/host unless already set).",
    )

    # Allow future flags without breaking; keep unknown args ignored for now.
    args, _unknown = parser.parse_known_args(argv)

    if args.ollama:
        os.environ.setdefault("NSPL_RUN_OLLAMA_INTEGRATION", "1")
        os.environ.setdefault("NSPL_OLLAMA_MODEL", "qwen3:0.6b")
        os.environ.setdefault("NSPL_OLLAMA_HOST", "http://localhost:11434")

    repo_root: Path = _find_repo_root(Path(__file__))

    # Critical: add repo root, not Core/, so "import Core.*" works.
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    loader: unittest.TestLoader = unittest.TestLoader()
    suite: unittest.TestSuite = unittest.TestSuite()

    tests_dirs: List[Path] = _find_tests_dirs(repo_root)
    if not tests_dirs:
        print("No Tests/ directories found under Core/ or Skills/.")
        return 0

    for tests_dir in tests_dirs:
        # top_level_dir pins package-import behavior to repo root
        discovered = loader.discover(
            start_dir=str(tests_dir),
            pattern="test_*.py",
            top_level_dir=str(repo_root),
        )
        suite.addTests(discovered)

    runner: unittest.TextTestRunner = unittest.TextTestRunner(verbosity=2)
    result: unittest.TestResult = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
