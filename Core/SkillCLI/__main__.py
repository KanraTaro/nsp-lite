"""
Core/SkillCLI/__main__.py

Allows:
  python -m Core.SkillCLI ...

Bootstrap rule:
- Put the *repo root* on sys.path so that `import Core.*` works.
- We locate the repo root by searching upward for:
    - a `.root` file
    - a `Core/` directory
"""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_repo_root_on_syspath() -> Path:
    current: Path = Path(__file__).resolve()

    # Walk up from this file until we find the repo root marker.
    probe: Path = current
    while True:
        candidate: Path = probe.parent
        if (candidate / ".root").is_file() and (candidate / "Core").is_dir():
            repo_root: Path = candidate
            repo_root_str: str = str(repo_root)

            # Insert at front so our repo wins over site-packages if names collide.
            if repo_root_str not in sys.path:
                sys.path.insert(0, repo_root_str)

            return repo_root

        # Stop at filesystem root
        if candidate == probe:
            break

        probe = candidate

    raise ModuleNotFoundError("NSP repo root not found (missing .root + Core/)")


_bootstrap_repo_root_on_syspath()

from Core.SkillCLI.skillcli import main as _main


if __name__ == "__main__":
    _main()

