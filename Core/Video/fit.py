from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FitMode(str, Enum):
    pad = "pad"   # keep whole image, add bars
    crop = "crop" # fill frame, crop edges


@dataclass(frozen=True)
class TargetSize:
    w: int
    h: int


def parse_target(target: str) -> TargetSize:
    # expects "WIDTHxHEIGHT"
    parts = target.lower().split("x")
    if len(parts) != 2:
        raise ValueError("target must be like 1080x1920")
    w = int(parts[0])
    h = int(parts[1])
    if w <= 0 or h <= 0:
        raise ValueError("target width/height must be > 0")
    return TargetSize(w=w, h=h)


def build_fit_filter(target: TargetSize, fit: FitMode) -> str:
    """
    Returns a filter chain that fits arbitrary input into target WxH.

    pad:
      scale to fit inside (decrease), then pad to center
    crop:
      scale to cover (increase), then crop to center
    """
    w = target.w
    h = target.h

    if fit == FitMode.pad:
        return (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        )

    if fit == FitMode.crop:
        return (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h}"
        )

    raise ValueError(f"Unknown fit mode: {fit}")

