from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Sequence

from Core.NSPL.Deps.deps import ExecutableInfo, ffmpeg_install_hints, require_executable


@dataclass(frozen=True)
class ProcResult:
    returncode: int
    stdout: str
    stderr: str


def require_ffmpeg() -> ExecutableInfo:
    return require_executable(
        "ffmpeg",
        env_vars=("NSP_FFMPEG",),
        install_hints=ffmpeg_install_hints(),
    )


def require_ffprobe() -> ExecutableInfo:
    return require_executable(
        "ffprobe",
        env_vars=("NSP_FFPROBE",),
        install_hints=ffmpeg_install_hints(),
    )


def run_ffmpeg(args: Sequence[str], *, timeout_sec: float | None = None) -> ProcResult:
    ffmpeg = require_ffmpeg()
    proc = subprocess.run(
        [ffmpeg.path, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    return ProcResult(proc.returncode, proc.stdout or "", proc.stderr or "")


def run_ffprobe(args: Sequence[str], *, timeout_sec: float | None = 3.0) -> ProcResult:
    ffprobe = require_ffprobe()
    proc = subprocess.run(
        [ffprobe.path, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    return ProcResult(proc.returncode, proc.stdout or "", proc.stderr or "")

