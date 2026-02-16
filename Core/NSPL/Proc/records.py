#!/usr/bin/env python3
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class ProcRecordType(str, Enum):
    START = "start"
    STDOUT = "stdout"
    STDERR = "stderr"
    PROGRESS = "progress"
    PHASE = "phase"
    DONE = "done"


def now_ts() -> float:
    return time.time()


def new_run_id() -> str:
    # Shortish but unique enough for local runs
    return uuid.uuid4().hex


@dataclass(frozen=True)
class ProcRecord:
    type: ProcRecordType
    run_id: str
    ts: float
    tool: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Enum -> string for clean JSON
        d["type"] = str(self.type.value)
        return d

