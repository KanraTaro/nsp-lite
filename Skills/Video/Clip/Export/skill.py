"""Video.Clip.Export skill.

Export a video using either:
- a .fffilter preset file (LookLab output)
- or a raw -vf filtergraph string

Optional:
- target WxH and fit mode (pad or crop)
- scale-width when no target is set
"""

from __future__ import annotations

import argparse
from typing import Any

from Core.Video.export import ExportOptions, export_video


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--in", dest="input_path", required=True, help="Input video path.")
    parser.add_argument("--out", dest="output_path", required=True, help="Output video path.")

    parser.add_argument("--look", dest="look_path", default=None, help="Path to .fffilter preset.")
    parser.add_argument("--vf", dest="vf", default=None, help="Raw ffmpeg -vf filtergraph string.")

    parser.add_argument("--preset", default="hq", choices=["hq", "fast", "social"], help="Encode preset.")

    parser.add_argument("--scale-width", type=int, default=None, help="Scale to width (keeps aspect). Ignored if --target is used.")
    parser.add_argument("--target", default=None, help="Target format WxH, e.g. 1080x1920.")
    parser.add_argument("--fit", default="pad", choices=["pad", "crop"], help="How to fit into target.")


def run(args: argparse.Namespace, ctx: Any) -> int:
    opts = ExportOptions(
        input_path=args.input_path,
        output_path=args.output_path,
        look_path=args.look_path,
        vf=args.vf,
        preset=args.preset,
        scale_width=args.scale_width,
        target=args.target,
        fit=args.fit,
    )

    export_video(opts)
    print(f"Wrote: {args.output_path}")
    return 0

