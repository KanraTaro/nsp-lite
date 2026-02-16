#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence, TextIO, Union

from .records import ProcRecord, ProcRecordType

from Core.NSPL.NodeCTX import (
    build_log_path,
    log_event_jsonl,
    JsonlRotationPolicy as NodeRotation,
    JsonlThrottlePolicy as NodeThrottle,
    utc_now_iso,
)

SubpathT = Optional[Union[str, Sequence[str]]]


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
    CLI-friendly sink.

    - Writes STDERR records to stderr.
    - Optionally writes STDOUT records too.
    - Prints PROGRESS percent as a single updating line.
    """

    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        show_stdout: bool = False,
        progress_throttle_s: float = 0.10,
    ) -> None:
        self.stream = stream if stream is not None else sys.stderr
        self.show_stdout = show_stdout
        self.progress_throttle_s = float(progress_throttle_s)
        self._last_progress_print: float = 0.0

    def on_record(self, rec: ProcRecord) -> None:
        if rec.type == ProcRecordType.STDERR:
            msg = str(rec.data.get("line", "") or "")
            if msg:
                self.stream.write(msg + "\n")
                self.stream.flush()
            return

        if rec.type == ProcRecordType.STDOUT and self.show_stdout:
            msg = str(rec.data.get("line", "") or "")
            if msg:
                self.stream.write(msg + "\n")
                self.stream.flush()
            return

        if rec.type == ProcRecordType.PROGRESS:
            pct = rec.data.get("pct", None)
            if pct is None:
                return

            now = time.time()
            if (now - self._last_progress_print) < self.progress_throttle_s:
                return
            self._last_progress_print = now

            phase = rec.data.get("phase", None)
            seg = rec.data.get("segment", None)

            left = f"{phase} " if phase else ""
            seg_txt = f"seg {seg} " if isinstance(seg, int) else ""

            self.stream.write(f"\r{left}{seg_txt}{int(pct):3d}%")
            self.stream.flush()
            return

        if rec.type == ProcRecordType.DONE:
            self.stream.write("\n")
            self.stream.flush()
            return


@dataclass(frozen=True)
class NodeCtxSinkConfig:
    root: Path
    instance_id: str
    node_tag: str
    domain: str
    global_scope: bool = False  # default FALSE for Proc runs
    subpath: SubpathT = None    # e.g. ["Proc", "ffmpeg"]
    rotation: Optional[NodeRotation] = None
    throttle: Optional[NodeThrottle] = None
    throttle_key: Optional[str] = None


class NodeCtxSink(EventSink):
    """
    Proc sink that routes everything through NodeCTX's single JSONL funnel.

    Writes to:
      State/<instance>/<node>/Logs/<domain>/<subpath>/...
    """

    def __init__(self, cfg: NodeCtxSinkConfig) -> None:
        self.cfg = cfg
        self._path: Optional[Path] = None

    def _ensure_path(self, run_id: str, tool: str) -> Path:
        if self._path is not None:
            return self._path

        # Default subpath includes Proc + tool name.
        subpath = self.cfg.subpath
        if subpath is None:
            subpath = ["Proc", tool]

        self._path = build_log_path(
            root=self.cfg.root,
            instance_id=self.cfg.instance_id,
            node_tag=self.cfg.node_tag,
            global_scope=self.cfg.global_scope,
            domain=self.cfg.domain,
            file_name=f"{run_id}.events.jsonl",
            subpath=subpath,
        )
        return self._path

    def on_record(self, rec: ProcRecord) -> None:
        path = self._ensure_path(rec.run_id, rec.tool)

        base = {
            # Human-readable + unix timestamp are both useful:
            "ts": utc_now_iso(),
            "ts_unix": float(rec.ts),
            "instance_id": self.cfg.instance_id,
            "node_tag": "Global" if self.cfg.global_scope else self.cfg.node_tag,
            "domain": self.cfg.domain,
            "run_id": rec.run_id,
            "tool": rec.tool,
        }

        kind = f"proc.{rec.type.value}"

        log_event_jsonl(
            path=path,
            kind=kind,
            base=base,
            extra={"data": rec.data},
            rotation=self.cfg.rotation,
            throttle=self.cfg.throttle,
            throttle_key=self.cfg.throttle_key,
        )

