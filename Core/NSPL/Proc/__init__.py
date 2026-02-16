"""
NSPL Proc: process execution + structured ProcRecords + optional adapters.

Design goals:
- Run external tools (ffmpeg, etc.) with consistent progress/log streaming.
- Emit ProcRecords to one or more sinks (JSONL file, console, callback).
- Keep core UI-agnostic (GUI can tail the JSONL file).
"""
from .records import ProcRecord, ProcRecordType, new_run_id, now_ts
from .sinks import EventSink, MultiSink, ConsoleSink, JsonlFileSink, CallbackSink
from .runner import ProcessRunner, RunResult

