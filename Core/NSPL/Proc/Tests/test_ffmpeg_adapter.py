#!/usr/bin/env python3
from __future__ import annotations

from Core.NSPL.Proc.adapters.ffmpeg import FfmpegAdapter, FfmpegAdapterConfig
from Core.NSPL.Proc.records import ProcRecordType


def test_ffmpeg_adapter_out_time_us_percent() -> None:
    run_id = "test"
    cfg = FfmpegAdapterConfig(duration_ms=10_000)
    a = FfmpegAdapter(run_id, cfg)

    recs = a.on_stdout_line("out_time_us=2500000")  # 2.5s
    assert len(recs) == 1
    assert recs[0].type == ProcRecordType.PROGRESS
    assert recs[0].data["pct"] == 25


def test_ffmpeg_adapter_segment_restart_when_time_goes_back() -> None:
    run_id = "test"
    cfg = FfmpegAdapterConfig(duration_ms=10_000)
    a = FfmpegAdapter(run_id, cfg)

    a.on_stdout_line("out_time_us=5000000")  # 5s
    recs = a.on_stdout_line("out_time_us=1000000")  # 1s (backwards)

    assert len(recs) == 2
    assert recs[0].type == ProcRecordType.PHASE
    assert recs[1].type == ProcRecordType.PROGRESS
    assert recs[1].data["segment"] == 2

