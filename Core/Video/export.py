from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from Core.Video.ffmpeg_exec import run_ffmpeg
from Core.Video.filters import compose_vf
from Core.Video.fit import FitMode, parse_target, build_fit_filter


@dataclass(frozen=True)
class ExportPreset:
    crf: str
    preset: str
    audio_codec: str
    audio_bitrate: str


def _get_preset(name: str) -> ExportPreset:
    n = name.strip().lower()
    if n == "fast":
        return ExportPreset(crf="20", preset="veryfast", audio_codec="aac", audio_bitrate="160k")
    if n == "social":
        return ExportPreset(crf="19", preset="fast", audio_codec="aac", audio_bitrate="192k")
    # default "hq"
    return ExportPreset(crf="18", preset="slow", audio_codec="aac", audio_bitrate="192k")


@dataclass(frozen=True)
class ExportOptions:
    input_path: str
    output_path: str
    look_path: Optional[str] = None     # .fffilter file
    vf: Optional[str] = None            # raw vf string
    preset: str = "hq"
    scale_width: Optional[int] = None
    target: Optional[str] = None        # "1080x1920"
    fit: str = "pad"                    # "pad" | "crop"


def _load_look_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def build_export_args(opts: ExportOptions) -> list[str]:
    if opts.look_path and opts.vf:
        raise ValueError("Use either look_path or vf, not both.")
    if not opts.look_path and not opts.vf:
        raise ValueError("You must provide look_path or vf.")

    look_vf = None
    if opts.look_path:
        look_vf = _load_look_text(opts.look_path)
    else:
        look_vf = opts.vf

    fit_vf = None
    scale_width = opts.scale_width

    if opts.target:
        target_size = parse_target(opts.target)
        fit_mode = FitMode(opts.fit)
        fit_vf = build_fit_filter(target_size, fit_mode)
        scale_width = None  # target controls sizing

    vf = compose_vf(
        look_vf=look_vf,
        fit_vf=fit_vf,
        scale_width=scale_width,
        force_yuv420p=True,
    )

    preset = _get_preset(opts.preset)

    # Always force +faststart for web friendliness
    args: list[str] = [
        "-y",
        "-hide_banner",
        "-nostats",
        "-i", opts.input_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", preset.crf,
        "-preset", preset.preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", preset.audio_codec,
        "-b:a", preset.audio_bitrate,
        opts.output_path,
    ]
    return args


def export_video(opts: ExportOptions) -> None:
    in_path = os.path.abspath(opts.input_path)
    out_path = os.path.abspath(opts.output_path)

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Input not found: {in_path}")

    args = build_export_args(ExportOptions(
        input_path=in_path,
        output_path=out_path,
        look_path=opts.look_path,
        vf=opts.vf,
        preset=opts.preset,
        scale_width=opts.scale_width,
        target=opts.target,
        fit=opts.fit,
    ))

    result = run_ffmpeg(args)
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        if err == "":
            err = "ffmpeg exited with a non-zero code."
        raise RuntimeError(err)

