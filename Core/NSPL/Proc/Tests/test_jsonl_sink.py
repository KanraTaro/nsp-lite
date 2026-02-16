#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile

from Core.NSPL.Proc.records import ProcRecord, ProcRecordType, now_ts
from Core.NSPL.Proc.sinks import JsonlFileSink, JsonlThrottlePolicy


def test_jsonl_sink_writes_lines() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "run.jsonl")
        sink = JsonlFileSink(path, throttle=JsonlThrottlePolicy(min_interval_s=0.0, pct_step=0))

        sink.on_record(ProcRecord(ProcRecordType.START, "r1", now_ts(), "tool", {"cmd": ["x"]}))
        sink.on_record(ProcRecord(ProcRecordType.PROGRESS, "r1", now_ts(), "tool", {"pct": 10}))
        sink.on_record(ProcRecord(ProcRecordType.DONE, "r1", now_ts(), "tool", {"exit_code": 0}))

        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]

        assert len(lines) == 3
        obj0 = json.loads(lines[0])
        assert obj0["type"] == "start"

