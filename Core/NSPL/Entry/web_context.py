from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
import os
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class SkillInvocationResult:
    exit_code: int
    stdout: str
    stderr: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "exit_code": int(self.exit_code),
            "stdout": str(self.stdout),
            "stderr": str(self.stderr),
        }


@dataclass(frozen=True)
class WebContext:
    repo_root: Path
    caller_cwd: Path
    web_root: Path
    app_dir: Path
    metadata: Dict[str, Any]
    entry_path: Path
    factory_name: str

    def run_skill(self, argv: List[str]) -> SkillInvocationResult:
        """Invoke the SkillCLI surface in-process and capture output.

        ``argv`` must use SkillCLI-surface shape, for example:
        ``["skill", "NSPL.Tools.Time.now", "--json"]``.
        """
        from Core.NSPL.Entry.Surfaces.skill_surface import main as skill_surface_main

        stdout = StringIO()
        stderr = StringIO()
        old_caller_cwd = os.environ.get("NSPL_CALLER_CWD")
        os.environ["NSPL_CALLER_CWD"] = str(self.caller_cwd)
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    result = skill_surface_main(list(argv))
                except SystemExit as e:
                    exit_code = int(e.code) if isinstance(e.code, int) else 1
                else:
                    exit_code = int(result) if isinstance(result, int) else 0
        finally:
            if old_caller_cwd is None:
                os.environ.pop("NSPL_CALLER_CWD", None)
            else:
                os.environ["NSPL_CALLER_CWD"] = old_caller_cwd

        return SkillInvocationResult(
            exit_code=exit_code,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
