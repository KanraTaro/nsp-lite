#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from ..records import ProcRecordType, RecordFragment


@dataclass
class FfmpegAdapterConfig:
    duration_ms: int = 0


class FfmpegAdapter:
    """
    Parses ffmpeg -progress output (recommended: -nostats -progress pipe:1).

    Feed stdout lines into on_stdout_line().

    Emits RecordFragments:
    - PROGRESS: { t_ms, dur_ms|None, pct|None, segment, phase="encode" }
    - PHASE: { segment, phase="segment_restart"|"segment_done" }
    """

    def __init__(self, cfg: FfmpegAdapterConfig) -> None:
        self.cfg = cfg
        self.segment: int = 1
        self.last_t_ms: int | None = None

    def _emit_phase(self, name: str) -> RecordFragment:
        return RecordFragment(
            type=ProcRecordType.PHASE,
            data={"segment": self.segment, "phase": name},
        )

    def _emit_progress(self, t_ms: int) -> RecordFragment:
        dur_ms = int(self.cfg.duration_ms) if int(self.cfg.duration_ms) > 0 else 0

        pct: int | None = None
        if dur_ms > 0:
            pct = int(max(0.0, min(100.0, (t_ms / dur_ms) * 100.0)))

        return RecordFragment(
            type=ProcRecordType.PROGRESS,
            data={
                "t_ms": t_ms,
                "dur_ms": dur_ms if dur_ms > 0 else None,
                "pct": pct,
                "segment": self.segment,
                "phase": "encode",
            },
        )

    def on_stdout_line(self, line: str) -> list[RecordFragment]:
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
                return [self._emit_phase("segment_done")]
            return []

        if out_time_us is None:
            return []

        t_ms = int(out_time_us / 1000)

        # Detect time going backwards: treat as new segment
        if self.last_t_ms is not None and (t_ms + 250) < self.last_t_ms:
            self.segment += 1
            self.last_t_ms = t_ms
            return [self._emit_phase("segment_restart"), self._emit_progress(t_ms)]

        self.last_t_ms = t_ms
        return [self._emit_progress(t_ms)]

    def on_stderr_line(self, line: str) -> list[RecordFragment]:
        # Optional fallback: parse stderr "time=00:00:..." lines later if needed.
        return []

