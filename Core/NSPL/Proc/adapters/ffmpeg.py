#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..records import ProcRecord, ProcRecordType, now_ts


@dataclass
class FfmpegAdapterConfig:
    duration_ms: int = 0
    tool_name: str = "ffmpeg"


class FfmpegAdapter:
    """
    Parses ffmpeg progress.

    Intended usage:
    - Run ffmpeg with: -nostats -progress pipe:1
    - Feed stdout lines into on_stdout_line()

    Emits:
    - PROGRESS records with pct (if duration known) and t_ms
    - PHASE records when a new "segment" appears (time jumps backward or progress=end)
    """

    def __init__(self, run_id: str, cfg: FfmpegAdapterConfig) -> None:
        self.run_id = run_id
        self.cfg = cfg

        self.segment: int = 1
        self.last_t_ms: int | None = None
        self.last_pct: int | None = None

    def _emit_progress(self, t_ms: int) -> ProcRecord:
        dur = int(self.cfg.duration_ms)
        pct: int | None = None
        if dur > 0:
            pct = int(max(0, min(100, (t_ms / dur) * 100.0)))

        data: dict[str, Any] = {
            "t_ms": t_ms,
            "dur_ms": dur if dur > 0 else None,
            "pct": pct,
            "segment": self.segment,
            "phase": "encode",
        }
        return ProcRecord(
            type=ProcRecordType.PROGRESS,
            run_id=self.run_id,
            ts=now_ts(),
            tool=self.cfg.tool_name,
            data=data,
        )

    def _emit_phase(self, name: str) -> ProcRecord:
        return ProcRecord(
            type=ProcRecordType.PHASE,
            run_id=self.run_id,
            ts=now_ts(),
            tool=self.cfg.tool_name,
            data={"segment": self.segment, "phase": name},
        )

    def on_stdout_line(self, line: str) -> list[ProcRecord]:
        ln = line.strip()
        if not ln:
            return []

        out_time_us: int | None = None

        if ln.startswith("out_time_us="):
            try:
                out_time_us = int(ln.split("=", 1)[1])
            except Exception:
                return []

        elif ln.startswith("out_time_ms="):
            try:
                v = int(ln.split("=", 1)[1])
                # Some builds still report microseconds here. Heuristic:
                out_time_us = v if v > 10_000_000 else v * 1000
            except Exception:
                return []

        elif ln.startswith("out_time="):
            # out_time=HH:MM:SS.micro
            try:
                ts = ln.split("=", 1)[1]
                parts = ts.split(":")
                if len(parts) == 3:
                    h = float(parts[0])
                    m = float(parts[1])
                    s = float(parts[2])
                    total_s = (h * 3600.0) + (m * 60.0) + s
                    out_time_us = int(total_s * 1_000_000.0)
            except Exception:
                return []

        elif ln.startswith("progress="):
            # progress=continue or progress=end
            if ln.endswith("end"):
                recs: list[ProcRecord] = [self._emit_phase("segment_done")]
                return recs
            return []

        if out_time_us is None:
            return []

        t_ms = int(out_time_us / 1000)

        # Detect time going backwards: treat as new segment
        if self.last_t_ms is not None and t_ms + 250 < self.last_t_ms:
            self.segment += 1
            self.last_t_ms = t_ms
            return [self._emit_phase("segment_restart"), self._emit_progress(t_ms)]

        self.last_t_ms = t_ms
        return [self._emit_progress(t_ms)]

    def on_stderr_line(self, line: str) -> list[ProcRecord]:
        # Optional fallback: parse stderr "time=00:00:..." lines later if needed.
        return []

