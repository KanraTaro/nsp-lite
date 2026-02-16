from __future__ import annotations

from Core.Video.ffmpeg_exec import run_ffprobe


def get_duration_ms(video_path: str) -> int:
    args = [
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = run_ffprobe(args, timeout_sec=3.0)
    if result.returncode != 0:
        return 0

    s = (result.stdout or "").strip()
    if s == "":
        return 0

    try:
        seconds = float(s)
        return int(seconds * 1000.0)
    except Exception:
        return 0

