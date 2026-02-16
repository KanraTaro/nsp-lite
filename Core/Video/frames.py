from __future__ import annotations

import glob
import os
import tempfile
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class PingPongOptions:
    frames_dir: str
    pattern: str = "*.png"
    require_min_frames: int = 3


def _natural_sort_key(path: str) -> List[object]:
    # Cheap “sort -V” style split for filenames: digits as ints, else strings
    import re
    base = os.path.basename(path)
    parts = re.split(r"(\d+)", base)
    key: List[object] = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p.lower())
    return key


def collect_frames(opts: PingPongOptions) -> List[str]:
    frames_dir = os.path.abspath(opts.frames_dir)
    matches = glob.glob(os.path.join(frames_dir, opts.pattern))
    matches_sorted = sorted(matches, key=_natural_sort_key)
    return matches_sorted


def build_pingpong_sequence(frames: Sequence[str]) -> List[str]:
    """
    Canon loop:
      Forward: A..Z
      Reverse: Z-1 .. B
    - skips duplicating Z
    - skips duplicating A (so looping looks smoother)
    Requires len(frames) >= 3.
    """
    if len(frames) < 3:
        raise ValueError("Need at least 3 frames for a clean ping-pong loop.")

    out: List[str] = []
    out.extend(frames)  # A..Z

    # reverse: Z-1 down to B  (index len-2 down to 1)
    i = len(frames) - 2
    while i > 0:
        out.append(frames[i])
        i -= 1

    return out


def _escape_concat_path(p: str) -> str:
    # ffmpeg concat demuxer expects:
    #   file 'path'
    # single quotes inside path must be escaped.
    return p.replace("'", r"'\''")


def write_concat_file(sequence: Sequence[str]) -> str:
    """
    Writes a concat demuxer list file into a temp dir and returns the file path.
    Caller owns cleanup (usually via TemporaryDirectory).
    """
    tmpdir = tempfile.mkdtemp(prefix="nspl_video_concat_")
    concat_path = os.path.join(tmpdir, "concat.txt")

    with open(concat_path, "w", encoding="utf-8") as f:
        for frame_path in sequence:
            abs_path = os.path.abspath(frame_path)
            safe = _escape_concat_path(abs_path)
            f.write(f"file '{safe}'\n")

    return concat_path

