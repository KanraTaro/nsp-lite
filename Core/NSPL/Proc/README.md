# NSPL Proc

NSPL Proc is a small, UI-agnostic process execution module for running external tools (ffmpeg, etc.) while streaming structured progress and logs.

It is designed to support both CLI and GUI usage without coupling to any particular UI framework.

## Core concepts

ProcRecord

* A structured event emitted during a process run.
* Fields: type, run_id, ts, tool, data

RecordFragment

* A partial record emitted by an adapter.
* Only contains: type + data
* The runner stamps run_id, ts, tool consistently.

EventSink

* A consumer of ProcRecords.
* Examples:

  * NodeCtxSink: default, NodeCTX JsonL funnel
  * ConsoleSink: terminal-friendly output
  * CallbackSink: push events into your own handler
  * MultiSink: fan-out to multiple sinks

Adapter

* Optional parser that converts raw stdout/stderr lines into RecordFragments.
* Example: FfmpegAdapter parses ffmpeg -progress output into PROGRESS/PHASE events.

## Directory layout

Core/NSPL/Proc/
    records.py   - ProcRecord, ProcRecordType, RecordFragment
    runner.py    - ProcessRunner
    sinks.py     - EventSink implementations
    adapters/    - Tool-specific line parsers (ffmpeg, etc.)
    Tests/       - unit tests

## Quick start

### JSONL logging (recommended for GUI + FPP)

Use `NodeCtxSink` to write structured events to a canonical JSONL file via NodeCTX.
A GUI can tail this file to drive progress bars and status panels.

Example:

* Create a sink:

  * `NodeCtxSink(NodeCtxSinkConfig(root=..., instance_id="main", node_tag="NodeA", domain="Proc"))`

  By default this writes to:

  `State/<instance>/<scope>/<domain>/Logs/<tool>/<run_id>.events.jsonl`

* Create a runner:

  * `ProcessRunner(sink)`

* Run a command:

  * `runner.run(["ffmpeg", ...], tool="ffmpeg", adapter=FfmpegAdapter(cfg), echo_stderr_lines=True)`

### CLI-friendly output

Use `ConsoleSink` for terminal feedback.
It prints stderr lines and shows progress as a single updating line.

### Fan-out (best of both)

Use `MultiSink` to write JSONL for GUI/FPP and also show CLI progress:

* `MultiSink([NodeCtxSink(...), ConsoleSink(...)])`

## Included sinks

NodeCtxSink

* Canonical JSONL output via NodeCTX (FPP-friendly)
* Optional rotation + throttling through NodeCTX policies

ConsoleSink

* Prints STDERR (and optionally STDOUT)
* Prints PROGRESS as a carriage-return line
* Throttles updates to avoid terminal spam

CallbackSink

* Calls a Python function for each record
* Useful for hooking into custom code or bridging into a UI layer

MultiSink

* Fans out events to multiple sinks

## Ffmpeg progress

To get reliable progress records from ffmpeg, run with:

* -nostats
* -progress pipe:1

The adapter consumes stdout lines like:

* out_time_us=...
* out_time_ms=...
* out_time=HH:MM:SS.micro
* progress=continue
* progress=end

The adapter emits:

* PROGRESS: includes t_ms, pct (if duration known), segment, phase
* PHASE: segment_restart when time jumps backward, segment_done when progress=end

## Notes and limitations

* ProcessRunner uses threads to consume stdout/stderr concurrently to avoid deadlocks.
* This module does not attempt to checkpoint or resume external tools, it only streams state.
* For long-running tasks, prefer NodeCtxSink so UI state can be reconstructed after restart by replaying the JSONL.

## Future extensions

* Additional adapters for other tools (sox, imagemagick, etc.)
* Optional stderr parsing for ffmpeg when -progress is not available
* Higher-level “ProcPipeline” helpers once multiple tool steps become common

