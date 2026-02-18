#!/usr/bin/env python3
from __future__ import annotations

import os
import queue
import time
import subprocess
import threading
from dataclasses import dataclass
from typing import Any, Protocol

from .records import ProcRecord, ProcRecordType, RecordFragment, new_run_id, now_ts
from .sinks import EventSink, MultiSink


class Adapter(Protocol):
    def on_stdout_line(self, line: str) -> list[RecordFragment]:
        ...

    def on_stderr_line(self, line: str) -> list[RecordFragment]:
        ...


@dataclass(frozen=True)
class RunResult:
    run_id: str
    exit_code: int
    tool: str
    cmd: list[str]
    
    
@dataclass(frozen=True)
class SpawnHandle:
    run_id: str
    tool: str
    cmd: list[str]
    proc: subprocess.Popen[str]


class ProcessRunner:
    """
    Subprocess-based runner (CLI-friendly).

    - Reads stdout/stderr concurrently (no deadlocks).
    - Emits ProcRecords to sinks.
    - Optional adapter transforms lines -> structured records (progress, phases).
    """

    def __init__(self, sink: EventSink) -> None:
        self.sink = sink

    def _emit(self, rec: ProcRecord) -> None:
        self.sink.on_record(rec)
    
    def _emit_fragments(self, run_id: str, tool_name: str, frags: list[RecordFragment]) -> None:
        for frag in frags:
            self._emit(
                ProcRecord(
                    type=frag.type,
                    run_id=run_id,
                    ts=now_ts(),
                    tool=tool_name,
                    data=frag.data,
                )
            )

    def spawn(
        self,
        cmd: list[str],
        *,
        tool: str | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> SpawnHandle:
        if not cmd:
            raise ValueError("cmd must be a non-empty list[str]")

        run_id = new_run_id()
        tool_name = tool if tool is not None else os.path.basename(cmd[0])

        self._emit(
            ProcRecord(
                type=ProcRecordType.START,
                run_id=run_id,
                ts=now_ts(),
                tool=tool_name,
                data={"cmd": cmd, "cwd": cwd, "mode": "spawn"},
            )
        )

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=None,
            stderr=None,
            text=True,
        )

        return SpawnHandle(run_id=run_id, tool=tool_name, cmd=cmd, proc=proc)

    def terminate(self, handle: SpawnHandle, *, kill_after_sec: float = 0.5) -> None:
        proc = handle.proc
        if proc.poll() is not None:
            return
        try:
            proc.terminate()
        except Exception:
            pass

        deadline = time.time() + float(kill_after_sec)
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.05)

        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

        exit_code = proc.poll()
        if exit_code is None:
            exit_code = 0

        self._emit(
            ProcRecord(
                type=ProcRecordType.DONE,
                run_id=handle.run_id,
                ts=now_ts(),
                tool=handle.tool,
                data={"exit_code": int(exit_code), "mode": "spawn"},
            )
        )

    def run(
        self,
        cmd: list[str],
        *,
        tool: str | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        adapter: Adapter | None = None,
        echo_stdout_lines: bool = False,
        echo_stderr_lines: bool = False,
        timeout_sec: float | None = None,
    ) -> RunResult:
        if not cmd:
            raise ValueError("cmd must be a non-empty list[str]")

        run_id = new_run_id()
        tool_name = tool if tool is not None else os.path.basename(cmd[0])

        self._emit(
            ProcRecord(
                type=ProcRecordType.START,
                run_id=run_id,
                ts=now_ts(),
                tool=tool_name,
                data={"cmd": cmd, "cwd": cwd},
            )
        )

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )

        q: queue.Queue[tuple[str, str]] = queue.Queue()

        def reader(stream, which: str) -> None:
            try:
                assert stream is not None
                for line in stream:
                    q.put((which, line.rstrip("\n")))
            finally:
                q.put((which, "__EOF__"))

        t_out = threading.Thread(target=reader, args=(proc.stdout, "stdout"), daemon=True)
        t_err = threading.Thread(target=reader, args=(proc.stderr, "stderr"), daemon=True)
        t_out.start()
        t_err.start()

        eof_out = False
        eof_err = False
        
        start_ts = time.time()
        timeout_s = float(timeout_sec) if timeout_sec is not None else None

        while True:
            # --- Timeout check (loop must wake up periodically) ---
            if timeout_s is not None:
                now = time.time()
                if (now - start_ts) > timeout_s:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    try:
                        proc.kill()
                    except Exception:
                        pass

                    exit_code = 124  # timeout conventional-ish
                    self._emit(
                        ProcRecord(
                            type=ProcRecordType.DONE,
                            run_id=run_id,
                            ts=now_ts(),
                            tool=tool_name,
                            data={"exit_code": exit_code, "timeout_sec": timeout_s},
                        )
                    )
                    return RunResult(run_id=run_id, exit_code=exit_code, tool=tool_name, cmd=cmd)

            # --- Read next line, but don't block forever ---
            try:
                which, line = q.get(timeout=0.1)
            except queue.Empty:
                # No output yet, loop again (so timeout can be re-checked)
                continue
                
            if line == "__EOF__":
                if which == "stdout":
                    eof_out = True
                else:
                    eof_err = True
                if eof_out and eof_err:
                    break
                continue

            if which == "stdout":
                if echo_stdout_lines:
                    self._emit(
                        ProcRecord(
                            type=ProcRecordType.STDOUT,
                            run_id=run_id,
                            ts=now_ts(),
                            tool=tool_name,
                            data={"line": line},
                        )
                    )
                if adapter is not None:
                    self._emit_fragments(run_id, tool_name, adapter.on_stdout_line(line))

            else:
                if echo_stderr_lines:
                    self._emit(
                        ProcRecord(
                            type=ProcRecordType.STDERR,
                            run_id=run_id,
                            ts=now_ts(),
                            tool=tool_name,
                            data={"line": line},
                        )
                    )
                if adapter is not None:
                    self._emit_fragments(run_id, tool_name, adapter.on_stderr_line(line))

        try:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
        except Exception:
            pass

        exit_code = proc.wait()

        self._emit(
            ProcRecord(
                type=ProcRecordType.DONE,
                run_id=run_id,
                ts=now_ts(),
                tool=tool_name,
                data={"exit_code": exit_code},
            )
        )

        return RunResult(run_id=run_id, exit_code=exit_code, tool=tool_name, cmd=cmd)

