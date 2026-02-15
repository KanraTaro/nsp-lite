#!/usr/bin/env python3
import os
import subprocess
import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSlider,
    QComboBox,
    QGroupBox,
)

# -------------------------
# Params + filter building
# -------------------------

@dataclass
class LookParams:
    # Basic grade
    contrast: float = 1.0
    saturation: float = 1.0
    brightness: float = 0.0
    gamma: float = 1.0

    # Detail / polish
    unsharp_luma: float = 0.0
    vignette: float = 0.0

    # "Extras"
    warmth: float = 0.0   # -1..+1 (cool -> warm)
    grain: float = 0.0    # 0..1

    # Output scale (0 = original, else width)
    scale_width: int = 0


def build_filter(p: LookParams) -> str:
    parts: list[str] = []

    # Scaling up front if requested (keeps everything consistent)
    if p.scale_width and p.scale_width > 0:
        parts.append(f"scale={p.scale_width}:-2:flags=lanczos")

    # Basic grade
    parts.append(
        f"eq=contrast={p.contrast:.3f}:"
        f"brightness={p.brightness:.3f}:"
        f"saturation={p.saturation:.3f}:"
        f"gamma={p.gamma:.3f}"
    )

    # Warmth/temperature-ish: small colorbalance shift
    # Positive warmth pushes reds up and blues down a bit.
    if abs(p.warmth) > 1e-4:
        # Keep this subtle. Too much will break anime skin tones fast.
        # rs/bs are "red shadows" / "blue shadows" style controls.
        rs = max(-0.25, min(0.25, 0.12 * p.warmth))
        bs = max(-0.25, min(0.25, -0.10 * p.warmth))
        parts.append(f"colorbalance=rs={rs:.3f}:bs={bs:.3f}")

    # Mild unsharp (only if requested)
    if p.unsharp_luma > 1e-4:
        # unsharp=luma_msize_x:luma_msize_y:luma_amount:chroma_msize_x:chroma_msize_y:chroma_amount
        parts.append(f"unsharp=5:5:{p.unsharp_luma:.3f}:5:5:0.000")

    # Vignette (only if requested)
    if p.vignette > 1e-4:
        # This is a simple strength mapping; it's not a perfect film vignette model,
        # but it's stable and gets the job done.
        angle = 0.2 + (p.vignette * 1.2)
        parts.append(f"vignette=PI/{1.0/angle:.3f}")

    # Grain (only if requested)
    if p.grain > 1e-4:
        # noise: alls is "strength". We keep it small; grain is easy to overdo.
        # 0..1 -> 0..12
        strength = max(0.0, min(12.0, p.grain * 12.0))
        parts.append(f"noise=alls={strength:.2f}:allf=t+u")

    # Always enforce a common pixel format for preview/export sanity
    parts.append("format=yuv420p")

    return ",".join(parts)


# -------------------------
# UI helpers
# -------------------------

def set_dark_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.Highlight, QColor(90, 120, 200))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)


class SliderRow(QWidget):
    """
    A simple slider + value label row that maps an int slider range to a float.
    I kept this tiny so you can keep adding knobs without pain.
    """
    def __init__(
        self,
        label: str,
        min_val: float,
        max_val: float,
        default_val: float,
        step: float,
        decimals: int = 3,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._min = float(min_val)
        self._max = float(max_val)
        self._step = float(step)
        self._decimals = int(decimals)

        # Slider works in ints. Convert float range to int ticks.
        self._ticks = int(round((self._max - self._min) / self._step))
        if self._ticks <= 0:
            self._ticks = 1

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label)
        self.label.setMinimumWidth(120)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self._ticks)
        self.slider.setSingleStep(1)

        self.value_label = QLabel("")
        self.value_label.setMinimumWidth(80)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)

        self.setLayout(layout)

        self.set_value(default_val)
        self.slider.valueChanged.connect(self._on_slider)

    def _on_slider(self, _: int) -> None:
        self.value_label.setText(f"{self.value():.{self._decimals}f}")

    def value(self) -> float:
        t = self.slider.value()
        v = self._min + (t * self._step)
        # Clamp (helps float rounding edge cases)
        if v < self._min:
            v = self._min
        if v > self._max:
            v = self._max
        return float(v)

    def set_value(self, v: float) -> None:
        v = float(v)
        if v < self._min:
            v = self._min
        if v > self._max:
            v = self._max
        t = int(round((v - self._min) / self._step))
        self.slider.setValue(t)
        self.value_label.setText(f"{self.value():.{self._decimals}f}")


# -------------------------
# Main app
# -------------------------

class LookLab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LookLab (ffplay preview)")
        self.preview_proc: subprocess.Popen | None = None

        root = QVBoxLayout()

        # Video path row
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Pick a video (ideally a 1–3s preview clip)")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_video)
        path_row.addWidget(QLabel("Video:"))
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        root.addLayout(path_row)

        # Scale dropdown
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItem("Original", 0)
        self.scale_combo.addItem("1080p wide (1920)", 1920)
        self.scale_combo.addItem("1440p wide (2560)", 2560)
        self.scale_combo.addItem("4K wide (3840)", 3840)
        scale_row.addWidget(self.scale_combo, 1)
        root.addLayout(scale_row)

        # Groups keep it readable
        grade_box = QGroupBox("Grade")
        grade_layout = QVBoxLayout()
        self.contrast = SliderRow("Contrast", 0.50, 2.50, 1.00, 0.01)
        self.saturation = SliderRow("Saturation", 0.00, 2.50, 1.00, 0.01)
        self.brightness = SliderRow("Brightness", -0.40, 0.40, 0.00, 0.01)
        self.gamma = SliderRow("Gamma", 0.50, 2.50, 1.00, 0.01)
        grade_layout.addWidget(self.contrast)
        grade_layout.addWidget(self.saturation)
        grade_layout.addWidget(self.brightness)
        grade_layout.addWidget(self.gamma)
        grade_box.setLayout(grade_layout)

        polish_box = QGroupBox("Polish")
        polish_layout = QVBoxLayout()
        self.unsharp_luma = SliderRow("Unsharp (luma)", 0.00, 2.00, 0.00, 0.01)
        self.vignette = SliderRow("Vignette", 0.00, 1.00, 0.00, 0.01)
        polish_layout.addWidget(self.unsharp_luma)
        polish_layout.addWidget(self.vignette)
        polish_box.setLayout(polish_layout)

        extras_box = QGroupBox("Extras")
        extras_layout = QVBoxLayout()
        self.warmth = SliderRow("Warmth", -1.00, 1.00, 0.00, 0.01)
        self.grain = SliderRow("Grain", 0.00, 1.00, 0.00, 0.01)
        extras_layout.addWidget(self.warmth)
        extras_layout.addWidget(self.grain)
        extras_box.setLayout(extras_layout)

        root.addWidget(grade_box)
        root.addWidget(polish_box)
        root.addWidget(extras_box)

        # Filter string display
        self.filter_edit = QLineEdit()
        self.filter_edit.setReadOnly(True)
        root.addWidget(QLabel("Generated -vf filtergraph:"))
        root.addWidget(self.filter_edit)

        # Buttons
        btns = QHBoxLayout()
        preview_btn = QPushButton("Preview (ffplay)")
        preview_btn.clicked.connect(self.preview)
        stop_btn = QPushButton("Stop Preview")
        stop_btn.clicked.connect(self.stop_preview)
        copy_btn = QPushButton("Copy Filter")
        copy_btn.clicked.connect(self.copy_filter)
        save_btn = QPushButton("Save Preset (.fffilter)")
        save_btn.clicked.connect(self.save_preset)
        export_btn = QPushButton("Export Video (ffmpeg)")
        export_btn.clicked.connect(self.export_video)

        btns.addWidget(preview_btn)
        btns.addWidget(stop_btn)
        btns.addWidget(copy_btn)
        btns.addWidget(save_btn)
        btns.addWidget(export_btn)
        root.addLayout(btns)

        self.setLayout(root)

        # Update filter string when values change
        for row in [self.contrast, self.saturation, self.brightness, self.gamma, self.unsharp_luma, self.vignette, self.warmth, self.grain]:
            row.slider.valueChanged.connect(self.update_filter)

        self.scale_combo.currentIndexChanged.connect(self.update_filter)

        self.update_filter()

    def get_params(self) -> LookParams:
        return LookParams(
            contrast=self.contrast.value(),
            saturation=self.saturation.value(),
            brightness=self.brightness.value(),
            gamma=self.gamma.value(),
            unsharp_luma=self.unsharp_luma.value(),
            vignette=self.vignette.value(),
            warmth=self.warmth.value(),
            grain=self.grain.value(),
            scale_width=int(self.scale_combo.currentData()),
        )

    def update_filter(self) -> None:
        filt = build_filter(self.get_params())
        self.filter_edit.setText(filt)

    def browse_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select video",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mov *.mkv *.webm);;All Files (*)",
        )
        if path:
            self.path_edit.setText(path)

    def preview(self) -> None:
        video = self.path_edit.text().strip()
        if not video:
            QMessageBox.warning(self, "No video", "Pick a video first (preferably a 1–3s preview clip).")
            return
        if not os.path.exists(video):
            QMessageBox.warning(self, "Missing file", f"File not found:\n{video}")
            return

        self.stop_preview()

        filt = self.filter_edit.text().strip()
        cmd = ["ffplay", "-loop", "0", "-vf", filt, video]
        try:
            self.preview_proc = subprocess.Popen(cmd)
        except FileNotFoundError:
            QMessageBox.critical(self, "ffplay not found", "ffplay wasn't found on PATH. Install ffmpeg / ffplay.")
        except Exception as ex:
            QMessageBox.critical(self, "Preview failed", str(ex))

    def stop_preview(self) -> None:
        if self.preview_proc and self.preview_proc.poll() is None:
            self.preview_proc.terminate()
        self.preview_proc = None

    def copy_filter(self) -> None:
        QApplication.clipboard().setText(self.filter_edit.text().strip())

    def save_preset(self) -> None:
        default_name = "look_01.fffilter"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save preset",
            default_name,
            "FFmpeg Filter (*.fffilter);;All Files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.filter_edit.text().strip() + "\n")
        except Exception as ex:
            QMessageBox.critical(self, "Save failed", str(ex))

    def export_video(self) -> None:
        video = self.path_edit.text().strip()
        if not video:
            QMessageBox.warning(self, "No video", "Pick a video first.")
            return
        if not os.path.exists(video):
            QMessageBox.warning(self, "Missing file", f"File not found:\n{video}")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export video",
            os.path.join(os.path.dirname(video), "exported.mp4"),
            "MP4 Video (*.mp4);;All Files (*)",
        )
        if not out_path:
            return

        filt = self.filter_edit.text().strip()

        # Keep this simple for now: good default encode for social posting
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            video,
            "-vf",
            filt,
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "slow",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            out_path,
        ]

        try:
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Export complete", f"Wrote:\n{out_path}")
        except FileNotFoundError:
            QMessageBox.critical(self, "ffmpeg not found", "ffmpeg wasn't found on PATH.")
        except subprocess.CalledProcessError as ex:
            QMessageBox.critical(self, "Export failed", f"ffmpeg failed.\n\n{ex}")


def main() -> int:
    app = QApplication(sys.argv)
    set_dark_palette(app)

    w = LookLab()
    w.resize(860, 520)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

