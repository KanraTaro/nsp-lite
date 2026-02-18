from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_repo_root_on_syspath() -> Path:
    current: Path = Path(__file__).resolve()
    probe: Path = current

    while True:
        candidate: Path = probe.parent
        if (candidate / ".root").is_file() and (candidate / "Core").is_dir():
            repo_root: Path = candidate
            repo_root_str: str = str(repo_root)
            if repo_root_str not in sys.path:
                sys.path.insert(0, repo_root_str)
            return repo_root

        if candidate == probe:
            break

        probe = candidate

    raise ModuleNotFoundError("NSP repo root not found (missing .root + Core/)")


_bootstrap_repo_root_on_syspath()

from Core.NSPL.GUICLI.guicli import main as _main


if __name__ == "__main__":
    _main()

