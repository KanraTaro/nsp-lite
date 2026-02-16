#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Callable, TextIO

from .records import ProcRecord, ProcRecordType


class EventSink:
    def on_record(self, rec: ProcRecord) -> None:
        raise NotImplementedError


class MultiSink(EventSink):
    def __init__(self, sinks: list[EventSink]) -> None:
        self.sinks: list[EventSink] = sinks

    def on_record(self, rec: ProcRecord) -> None:
        for s in self.sinks:
            s.on_record(rec)


class CallbackSink(EventSink):
    def __init__(self, cb: Callable[[ProcRecord], None]) -> None:
        self.cb = cb

    def on_record(self, rec: ProcRecord) -> None:
        self.cb(rec)


class ConsoleSink(EventSink):
    """
    Simple sink for CLI usage.
    - Logs stdout/stderr lines.
    - Prints progress updates as a single line (carriage return).
    """

    def __init__(self, stream: TextIO | None = None, show_stdout: bool = False) -> None:
        self.stream = stream if stream is not None else sys.stderr
        self.show_stdout = show_stdout
        self._last_progress_print: float = 0.0

    def on_record(self, rec: ProcRecord) -> None:
        if rec.type == ProcRecordType.STDERR:
            msg = rec.data.get("line", "")
            if msg:
                self.stream.write(msg + "\n")
                self.stream.flush()

        elif rec.type == ProcRecordType.STDOUT and self.show_stdout:
            msg = rec.data.get("line", "")
            if msg:
                self.stream.write(msg + "\n")
                self.stream.flush()

        elif rec.type == ProcRecordType.PROGRESS:
            pct = rec.data.get("pct", None)
            phase = rec.data.get("phase", None)
            seg = rec.data.get("segment", None)

            now = time.time()
            # Small throttle so we don't spam terminals
            if now - self._last_progress_print < 0.10:
                return
            self._last_progress_print = now

            if pct is None:
                return

            left = f"{phase} " if phase else ""
            seg_txt = f"seg {seg} " if isinstance(seg, int) else ""
            self.stream.write(f"\r{left}{seg_txt}{pct:3d}%")
            self.stream.flush()

        elif rec.type == ProcRecordType.DONE:
            # end the progress line cleanly
            self.stream.write("\n")
            self.stream.flush()


@dataclass
class JsonlThrottlePolicy:
    min_interval_s: float = 0.15
    pct_step: int = 1  # only write if pct changed by at least this


class JsonlFileSink(EventSink):
    """
    Append-only JSONL sink.

    Notes:
    - Flushes every record for safety.
    - Can throttle progress records (recommended).
    """

    def __init__(
        self,
        path: str,
        throttle: JsonlThrottlePolicy | None = None,
    ) -> None:
        self.path = path
        self.throttle = throttle

        self._f: TextIO | None = None
        self._last_progress_ts: float = 0.0
        self._last_progress_pct: int | None = None

        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _open(self) -> TextIO:
        if self._f is None:
            self._f = open(self.path, "a", encoding="utf-8")
        return self._f

    def close(self) -> None:
        if self._f is not None:
            try:
                self._f.flush()
                self._f.close()
            finally:
                self._f = None

    def _should_write_progress(self, rec: ProcRecord) -> bool:
        if self.throttle is None:
            return True

        pct = rec.data.get("pct", None)
        if pct is None:
            return True

        now = rec.ts
        if (now - self._last_progress_ts) < self.throttle.min_interval_s:
            # only allow if pct jumped a lot
            if self._last_progress_pct is None:
                return False
            if abs(int(pct) - int(self._last_progress_pct)) < self.throttle.pct_step:
                return False

        return True

    def on_record(self, rec: ProcRecord) -> None:
        if rec.type == ProcRecordType.PROGRESS and not self._should_write_progress(rec):
            return

        f = self._open()
        f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        f.flush()

        if rec.type == ProcRecordType.PROGRESS:
            self._last_progress_ts = rec.ts
            pct = rec.data.get("pct", None)
            if pct is not None:
                self._last_progress_pct = int(pct)

        if rec.type == ProcRecordType.DONE:
            self.close()

