from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from Core.Video.ffmpeg_exec import run_ffmpeg
from Core.Video.frames import PingPongOptions, build_pingpong_sequence, collect_frames


@dataclass(frozen=True)
class FramesToVideoOptions:
    frames_dir: str
    output_path: str
    fps: int = 12
    pattern: str = "*.png"
    mode: str = "pingpong"  # "forward" | "pingpong"

    # Encoding
    vcodec: str = "libx264"
    crf: str = "18"
    preset: str = "veryfast"
    pix_fmt: str = "yuv420p"
    movflags: str = "+faststart"

    # Optional sizing
    scale_width: Optional[int] = None  # scale=WIDTH:-2

    # Progress
    include_progress: bool = True


@dataclass(frozen=True)
class PreparedFramesToVideo:
    args: List[str]               # ffmpeg args only, no exe path
    duration_ms: int              # best-effort duration for percent
    frame_count: int              # original frame count, before pingpong expansion
    sequence_count: int           # actual concat list length
    cleanup: Callable[[], None]   # must be called by caller


def _validate_mode(mode: str) -> str:
    m = (mode or "").strip().lower()
    if m not in ("forward", "pingpong"):
        raise ValueError("mode must be 'forward' or 'pingpong'")
    return m


def _estimate_duration_ms(sequence_count: int, fps: int) -> int:
    if fps <= 0 or sequence_count <= 0:
        return 0
    seconds = float(sequence_count) / float(fps)
    return int(seconds * 1000.0)


def _write_concat_file_in_tmp(sequence: Sequence[str]) -> Tuple[str, Callable[[], None]]:
    tmpdir_obj = tempfile.TemporaryDirectory(prefix="nspl_video_concat_")
    tmpdir = tmpdir_obj.name
    concat_path = os.path.join(tmpdir, "concat.txt")

    def _escape_concat_path(p: str) -> str:
        return p.replace("'", r"'\''")

    with open(concat_path, "w", encoding="utf-8") as f:
        for frame_path in sequence:
            abs_path = os.path.abspath(frame_path)
            safe = _escape_concat_path(abs_path)
            f.write(f"file '{safe}'\n")

    def _cleanup() -> None:
        try:
            tmpdir_obj.cleanup()
        except Exception:
            pass

    return concat_path, _cleanup


def prepare_frames_to_video(opts: FramesToVideoOptions) -> PreparedFramesToVideo:
    frames_dir = os.path.abspath(opts.frames_dir)
    out_path = os.path.abspath(opts.output_path)

    if not os.path.isdir(frames_dir):
        raise FileNotFoundError(f"Frames dir not found: {frames_dir}")

    if opts.fps <= 0:
        raise ValueError("fps must be > 0")

    mode = _validate_mode(opts.mode)

    pp_opts = PingPongOptions(frames_dir=frames_dir, pattern=opts.pattern, require_min_frames=3)
    frames = collect_frames(pp_opts)

    if len(frames) < pp_opts.require_min_frames:
        raise ValueError(f"Need at least {pp_opts.require_min_frames} frames, found {len(frames)}")

    if mode == "pingpong":
        sequence = build_pingpong_sequence(frames)
    else:
        sequence = list(frames)

    concat_path, cleanup = _write_concat_file_in_tmp(sequence)

    duration_ms = _estimate_duration_ms(sequence_count=len(sequence), fps=int(opts.fps))

    # Build ffmpeg args (concat demuxer)
    args: List[str] = [
        "-y",
        "-hide_banner",
        "-nostats",
        "-loglevel", "error",
    ]

    if opts.include_progress:
        args.extend(["-progress", "pipe:1"])

    args.extend([
        "-r", str(int(opts.fps)),
        "-f", "concat",
        "-safe", "0",
        "-i", concat_path,
    ])

    vf_parts: List[str] = []
    if opts.scale_width is not None and int(opts.scale_width) > 0:
        vf_parts.append(f"scale={int(opts.scale_width)}:-2")

    # Always force pix fmt for broad compatibility
    vf_parts.append(f"format={opts.pix_fmt}")

    args.extend([
        "-vf", ",".join(vf_parts),
        "-c:v", opts.vcodec,
        "-crf", str(opts.crf),
        "-preset", str(opts.preset),
        "-pix_fmt", opts.pix_fmt,
        "-movflags", opts.movflags,
        out_path,
    ])

    return PreparedFramesToVideo(
        args=args,
        duration_ms=duration_ms,
        frame_count=len(frames),
        sequence_count=len(sequence),
        cleanup=cleanup,
    )


def frames_to_video(opts: FramesToVideoOptions) -> None:
    """
    Convenience sync wrapper, mainly for Skills or tests.
    GUI should prefer prepare_frames_to_video() and run ffmpeg via QProcess.
    """
    prep = prepare_frames_to_video(opts)
    try:
        result = run_ffmpeg(prep.args, timeout_sec=None, sink=None, capture_stdout=True, capture_stderr=True)
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            if err == "":
                err = "ffmpeg exited with a non-zero code."
            raise RuntimeError(err)
    finally:
        prep.cleanup()

