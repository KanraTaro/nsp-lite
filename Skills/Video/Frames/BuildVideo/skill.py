"""Video.Frames.BuildVideo skill.

General frames-to-video builder.

Supports:
- forward sequence
- pingpong sequence

This is the canonical CLI/agent-facing entrypoint for turning a folder
of ordered frames into a video clip.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from Core.Video.frames_to_video import FramesToVideoOptions, frames_to_video


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--frames-dir", default=".", help="Folder containing frames.")
    parser.add_argument("--glob", default="*.png", help="Glob pattern (default: *.png).")
    parser.add_argument("--fps", type=int, default=12, help="Frames per second.")
    parser.add_argument("--out", default="frames.mp4", help="Output filename or path.")

    parser.add_argument(
        "--mode",
        default="forward",
        choices=["forward", "pingpong"],
        help="Sequence mode.",
    )

    parser.add_argument("--crf", default="18", help="x264 CRF value.")
    parser.add_argument("--preset", default="veryfast", help="x264 preset.")
    parser.add_argument("--codec", default="libx264", help="Video codec (default: libx264).")
    parser.add_argument(
        "--scale-width",
        type=int,
        default=None,
        help="Optional output width. Keeps aspect ratio with even height.",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    frames_dir = os.path.abspath(args.frames_dir)

    out_path = args.out
    if not os.path.isabs(out_path):
        out_path = os.path.join(frames_dir, out_path)

    opts = FramesToVideoOptions(
        frames_dir=frames_dir,
        output_path=out_path,
        fps=int(args.fps),
        pattern=str(args.glob),
        mode=str(args.mode),
        vcodec=str(args.codec),
        crf=str(args.crf),
        preset=str(args.preset),
        scale_width=args.scale_width,
        include_progress=False,
    )

    frames_to_video(opts)

    print(f"Wrote: {out_path}")
    return 0
