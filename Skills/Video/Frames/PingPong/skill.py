"""Video.Frames.PingPong skill.

Build a clean ping-pong loop from a folder of frames and encode to a video.

Canon loop shape:
  Forward: A..Z
  Reverse: Z-1..B
(no duplicated A or Z, looks smoother when looping)
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from typing import Any

from Core.Video.frames import PingPongOptions, collect_frames, build_pingpong_sequence, write_concat_file
from Core.Video.ffmpeg_exec import run_ffmpeg


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--frames-dir", default=".", help="Folder containing frames.")
    parser.add_argument("--glob", default="*.png", help="Glob pattern (default: *.png).")
    parser.add_argument("--fps", type=int, default=12, help="Frames per second.")
    parser.add_argument("--out", default="pingpong.mp4", help="Output filename or path.")
    parser.add_argument("--crf", default="18", help="x264 CRF value.")
    parser.add_argument("--preset", default="veryfast", help="x264 preset.")
    parser.add_argument("--codec", default="libx264", help="Video codec (default: libx264).")


def run(args: argparse.Namespace, ctx: Any) -> int:
    frames_dir = os.path.abspath(args.frames_dir)
    pattern = args.glob

    opts = PingPongOptions(frames_dir=frames_dir, pattern=pattern)
    frames = collect_frames(opts)
    if len(frames) < 3:
        raise SystemExit("Need at least 3 frames for a clean ping-pong loop.")

    seq = build_pingpong_sequence(frames)

    # concat file lives in a temp folder, clean it afterward
    concat_path = write_concat_file(seq)
    concat_dir = os.path.dirname(concat_path)

    try:
        out_path = args.out
        if not os.path.isabs(out_path):
            out_path = os.path.join(frames_dir, out_path)

        ff_args = [
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-r", str(args.fps),
            "-f", "concat",
            "-safe", "0",
            "-i", concat_path,
            "-vf", "format=yuv420p",
            "-c:v", str(args.codec),
            "-crf", str(args.crf),
            "-preset", str(args.preset),
            out_path,
        ]

        result = run_ffmpeg(ff_args)
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            if err == "":
                err = "ffmpeg exited with a non-zero code."
            raise SystemExit(err)

        print(f"Wrote: {out_path}")
        return 0

    finally:
        shutil.rmtree(concat_dir, ignore_errors=True)

