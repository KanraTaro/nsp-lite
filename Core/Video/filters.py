from __future__ import annotations

from typing import Optional


def compose_vf(
    *,
    look_vf: Optional[str],
    fit_vf: Optional[str],
    scale_width: Optional[int],
    force_yuv420p: bool = True,
) -> str:
    """
    Compose a safe -vf string. Order:
      look -> fit -> scale_width (only if no fit) -> format
    """
    parts: list[str] = []

    if look_vf is not None and look_vf.strip() != "":
        parts.append(look_vf.strip())

    if fit_vf is not None and fit_vf.strip() != "":
        parts.append(fit_vf.strip())
    else:
        if scale_width is not None and scale_width > 0:
            # Keep aspect ratio, ensure even width/height
            parts.append(f"scale={scale_width}:-2")

    if force_yuv420p:
        parts.append("format=yuv420p")

    return ",".join(parts)

