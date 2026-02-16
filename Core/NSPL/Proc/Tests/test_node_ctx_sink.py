from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from Core.NSPL.Proc.records import ProcRecord, ProcRecordType, now_ts
from Core.NSPL.Proc.sinks import NodeCtxSink, NodeCtxSinkConfig


def test_node_ctx_sink_writes_jsonl_lines() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        sink = NodeCtxSink(
            NodeCtxSinkConfig(
                root=root,
                instance_id="main",
                node_tag="nodeA",
                domain="Proc",
                global_scope=False,
            )
        )

        r1 = ProcRecord(ProcRecordType.START, "run1", now_ts(), "ffmpeg", {"cmd": ["ffmpeg"]})
        r2 = ProcRecord(ProcRecordType.PROGRESS, "run1", now_ts(), "ffmpeg", {"pct": 10})
        r3 = ProcRecord(ProcRecordType.DONE, "run1", now_ts(), "ffmpeg", {"exit_code": 0})

        sink.on_record(r1)
        sink.on_record(r2)
        sink.on_record(r3)

        # Path should be under:
        # State/main/nodeA/Proc/Logs/ffmpeg/run1.events.jsonl
        log_path = root / "State" / "main" / "nodeA" / "Proc" / "Logs" / "ffmpeg" / "run1.events.jsonl"

        assert log_path.exists()

        lines = [ln.strip() for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 3

        obj0 = json.loads(lines[0])
        assert obj0["kind"] == "proc.start"
        assert obj0["run_id"] == "run1"
        assert obj0["tool"] == "ffmpeg"

