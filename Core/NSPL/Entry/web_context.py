from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Sequence


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

    def _skill_subprocess_command(self, argv: Sequence[str]) -> List[str]:
        return [
            sys.executable,
            str(self.repo_root / "nspl.py"),
            "--root",
            str(self.repo_root),
            "--cwd",
            str(self.caller_cwd),
            "skill",
            *list(argv),
        ]

    def run_skill(self, argv: List[str], timeout: float = 30.0) -> SkillInvocationResult:
        """Invoke a SkillCLI command through the real NSPL gateway path."""
        return self.run_skill_subprocess(argv, timeout=timeout)

    def run_skill_subprocess(self, argv: List[str], timeout: float = 30.0) -> SkillInvocationResult:
        """Invoke a SkillCLI command in a subprocess and capture output.

        ``argv`` must use SkillCLI-surface shape, for example:
        ``["skill", "NSPL.Tools.Time.now", "--json"]``.
        """
        command = self._skill_subprocess_command(argv)
        env = os.environ.copy()

        try:
            completed = subprocess.run(
                command,
                cwd=str(self.repo_root),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            stderr = e.stderr or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            message = f"Skill invocation timed out after {timeout:g} seconds"
            if stderr:
                message = f"{message}\n{stderr}"
            return SkillInvocationResult(
                exit_code=124,
                stdout=(e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else e.stdout or ""),
                stderr=message,
            )
        except OSError as e:
            return SkillInvocationResult(exit_code=1, stdout="", stderr=f"Skill invocation failed: {e}")

        return SkillInvocationResult(
            exit_code=int(completed.returncode),
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def run_skill_inprocess(self, argv: List[str]) -> SkillInvocationResult:
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
