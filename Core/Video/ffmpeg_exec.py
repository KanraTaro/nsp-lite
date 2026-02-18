from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from Core.NSPL.Deps.deps import ExecutableInfo, ffmpeg_install_hints, require_executable
from Core.NSPL.Proc.records import ProcRecord, ProcRecordType
from Core.NSPL.Proc.runner import ProcessRunner, RunResult
from Core.NSPL.Proc.sinks import CallbackSink, EventSink, MultiSink


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


def require_ffplay() -> ExecutableInfo:
    return require_executable(
        "ffplay",
        env_vars=("NSP_FFPLAY",),
        install_hints=ffmpeg_install_hints(),
    )


class _Capture:
    def __init__(self) -> None:
        self.stdout_lines: list[str] = []
        self.stderr_lines: list[str] = []

    def on_record(self, rec: ProcRecord) -> None:
        if rec.type == ProcRecordType.STDOUT:
            line = str(rec.data.get("line", "") or "")
            if line != "":
                self.stdout_lines.append(line)
            return

        if rec.type == ProcRecordType.STDERR:
            line = str(rec.data.get("line", "") or "")
            if line != "":
                self.stderr_lines.append(line)
            return

    def stdout_text(self) -> str:
        if len(self.stdout_lines) == 0:
            return ""
        return "\n".join(self.stdout_lines) + "\n"

    def stderr_text(self) -> str:
        if len(self.stderr_lines) == 0:
            return ""
        return "\n".join(self.stderr_lines) + "\n"


def _run_tool_via_proc(
    *,
    exe_path: str,
    args: Sequence[str],
    tool_name: str,
    timeout_sec: float | None,
    sink: Optional[EventSink],
    capture_stdout: bool,
    capture_stderr: bool,
) -> ProcResult:
    capture = _Capture()
    capture_sink = CallbackSink(capture.on_record)

    final_sink: EventSink
    if sink is None:
        final_sink = capture_sink
    else:
        final_sink = MultiSink([sink, capture_sink])

    runner = ProcessRunner(final_sink)

    run_result: RunResult = runner.run(
        [exe_path, *list(args)],
        tool=tool_name,
        adapter=None,
        echo_stdout_lines=bool(capture_stdout),
        echo_stderr_lines=bool(capture_stderr),
        timeout_sec=timeout_sec,
    )

    return ProcResult(
        returncode=int(run_result.exit_code),
        stdout=capture.stdout_text(),
        stderr=capture.stderr_text(),
    )


def run_ffmpeg(
    args: Sequence[str],
    *,
    timeout_sec: float | None = None,
    sink: Optional[EventSink] = None,
    capture_stdout: bool = True,
    capture_stderr: bool = True,
) -> ProcResult:
    ffmpeg = require_ffmpeg()
    return _run_tool_via_proc(
        exe_path=ffmpeg.path,
        args=args,
        tool_name="ffmpeg",
        timeout_sec=timeout_sec,
        sink=sink,
        capture_stdout=capture_stdout,
        capture_stderr=capture_stderr,
    )


def run_ffprobe(
    args: Sequence[str],
    *,
    timeout_sec: float | None = 3.0,
    sink: Optional[EventSink] = None,
    capture_stdout: bool = True,
    capture_stderr: bool = True,
) -> ProcResult:
    ffprobe = require_ffprobe()
    return _run_tool_via_proc(
        exe_path=ffprobe.path,
        args=args,
        tool_name="ffprobe",
        timeout_sec=timeout_sec,
        sink=sink,
        capture_stdout=capture_stdout,
        capture_stderr=capture_stderr,
    )


def run_ffplay(
    args: Sequence[str],
    *,
    timeout_sec: float | None = None,
    sink: Optional[EventSink] = None,
    capture_stdout: bool = False,
    capture_stderr: bool = True,
) -> ProcResult:
    ffplay = require_ffplay()
    return _run_tool_via_proc(
        exe_path=ffplay.path,
        args=args,
        tool_name="ffplay",
        timeout_sec=timeout_sec,
        sink=sink,
        capture_stdout=capture_stdout,
        capture_stderr=capture_stderr,
    )

