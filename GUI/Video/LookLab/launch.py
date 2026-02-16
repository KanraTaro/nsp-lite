#!/usr/bin/env python3
import os
import subprocess
import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt, QProcess
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
    QDoubleSpinBox,
    QProgressDialog,
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
    if abs(p.warmth) > 1e-4:
        rs = max(-0.25, min(0.25, 0.12 * p.warmth))
        bs = max(-0.25, min(0.25, -0.10 * p.warmth))
        parts.append(f"colorbalance=rs={rs:.3f}:bs={bs:.3f}")

    # Mild unsharp (only if requested)
    if p.unsharp_luma > 1e-4:
        parts.append(f"unsharp=5:5:{p.unsharp_luma:.3f}:5:5:0.000")

    # Vignette (only if requested)
    if p.vignette > 1e-4:
        angle = 0.2 + (p.vignette * 1.2)
        parts.append(f"vignette=PI/{1.0/angle:.3f}")

    # Grain (only if requested)
    if p.grain > 1e-4:
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
    Slider + editable float spinbox.
    Slider gives fast feel, spinbox gives precision.
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
        self._sync_guard: bool = False

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

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(self._decimals)
        self.spin.setRange(self._min, self._max)
        self.spin.setSingleStep(self._step)
        self.spin.setKeyboardTracking(False)
        self.spin.setMinimumWidth(90)

        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)

        self.setLayout(layout)

        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)

        self.set_value(default_val)

    def _on_slider(self, t: int) -> None:
        if self._sync_guard:
            return
        self._sync_guard = True
        v = self._min + (t * self._step)
        v = max(self._min, min(self._max, v))
        self.spin.setValue(v)
        self._sync_guard = False

    def _on_spin(self, v: float) -> None:
        if self._sync_guard:
            return
        self._sync_guard = True
        v2 = max(self._min, min(self._max, float(v)))
        t = int(round((v2 - self._min) / self._step))
        self.slider.setValue(t)
        self._sync_guard = False

    def value(self) -> float:
        return float(self.spin.value())

    def set_value(self, v: float) -> None:
        self.spin.setValue(float(v))


# -------------------------
# Main app
# -------------------------

class LookLab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LookLab (ffplay preview)")

        self.preview_proc: subprocess.Popen | None = None

        # Export state (async)
        self.export_proc: QProcess | None = None
        self.export_progress: QProgressDialog | None = None
        self.export_duration_ms: int = 0
        self.export_out_path: str = ""
        self.export_progress_buf: str = ""

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
        scale_row.addWidget(QLabel("Scale width:"))
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
        self.vignette = SliderRow("Vignette", 0.00, 1.00, 0.00, 0.001, decimals=3)
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

        # Update filter string when values change (slider + spinbox!)
        for row in [self.contrast, self.saturation, self.brightness, self.gamma, self.unsharp_luma, self.vignette, self.warmth, self.grain]:
            row.slider.valueChanged.connect(self.update_filter)
            row.spin.valueChanged.connect(self.update_filter)

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

    # -------------------------
    # Export (async + percent)
    # -------------------------

    def get_duration_ms(self, video_path: str) -> int:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            s = result.stdout.strip()
            if not s:
                return 0
            seconds = float(s)
            return int(seconds * 1000.0)
        except Exception:
            return 0

    def _cancel_export(self) -> None:
        if self.export_proc is not None:
            self.export_proc.kill()

    def _on_export_stdout(self) -> None:
        if self.export_proc is None or self.export_progress is None:
            return

        chunk = bytes(self.export_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not chunk:
            return

        self.export_progress_buf += chunk

        # Only parse complete lines, keep the last partial line in the buffer
        lines = self.export_progress_buf.splitlines(keepends=False)
        if self.export_progress_buf and not self.export_progress_buf.endswith("\n"):
            self.export_progress_buf = lines[-1] if lines else self.export_progress_buf
            lines = lines[:-1]
        else:
            self.export_progress_buf = ""

        out_time_us: int | None = None

        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue

            # ffmpeg variants:
            # out_time_us=12345678
            # out_time_ms=12345   (sometimes microseconds anyway, depends)
            # out_time=00:00:01.23
            if ln.startswith("out_time_us="):
                try:
                    out_time_us = int(ln.split("=", 1)[1])
                except Exception:
                    pass

            elif ln.startswith("out_time_ms="):
                try:
                    v = int(ln.split("=", 1)[1])
                    # Many builds lie and still report microseconds here. Heuristic:
                    out_time_us = v if v > 10_000_000 else v * 1000
                except Exception:
                    pass

            elif ln.startswith("out_time="):
                # Parse hh:mm:ss.micro
                try:
                    ts = ln.split("=", 1)[1]
                    parts = ts.split(":")
                    if len(parts) == 3:
                        h = float(parts[0])
                        m = float(parts[1])
                        s = float(parts[2])
                        total_s = (h * 3600.0) + (m * 60.0) + s
                        out_time_us = int(total_s * 1_000_000.0)
                except Exception:
                    pass

            elif ln.startswith("progress=") and ln.endswith("end"):
                self.export_progress.setValue(100)

        if out_time_us is None:
            return

        # Convert to ms for comparing with duration_ms
        t_ms = int(out_time_us / 1000)

        if self.export_duration_ms > 0:
            pct = int(max(0, min(100, (t_ms / self.export_duration_ms) * 100.0)))
            self.export_progress.setValue(pct)

    def _on_export_finished(self, exit_code: int, _status) -> None:
        if self.export_progress is not None:
            if exit_code == 0:
                self.export_progress.setValue(100)
            self.export_progress.close()
            self.export_progress = None

        if exit_code == 0:
            QMessageBox.information(self, "Export complete", f"Wrote:\n{self.export_out_path}")
        else:
            err = ""
            if self.export_proc is not None:
                err = bytes(self.export_proc.readAllStandardError()).decode("utf-8", errors="replace")
            if not err.strip():
                err = "ffmpeg exited with a non-zero code."
            QMessageBox.critical(self, "Export failed", err.strip())

        self.export_proc = None
        self.export_out_path = ""
        self.export_duration_ms = 0

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

        # Kill any previous export
        if self.export_proc is not None:
            try:
                self.export_proc.kill()
            except Exception:
                pass
            self.export_proc = None

        self.export_out_path = out_path
        self.export_duration_ms = self.get_duration_ms(video)

        filt = self.filter_edit.text().strip()

        args = [
            "-y",
            "-hide_banner",
            "-nostats",
            "-progress", "pipe:1",
            "-i", video,
            "-vf", filt,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "192k",
            out_path,
        ]

        self.export_proc = QProcess(self)
        self.export_proc.setProgram("ffmpeg")
        self.export_proc.setArguments(args)
        self.export_proc.setProcessChannelMode(QProcess.SeparateChannels)

        self.export_progress = QProgressDialog("Exporting...", "Cancel", 0, 100, self)
        self.export_progress.setWindowTitle("LookLab Export")
        self.export_progress.setMinimumDuration(0)
        self.export_progress.setValue(0)
        self.export_progress.canceled.connect(self._cancel_export)

        # If we couldn't read duration, show an indeterminate spinner-style bar.
        if self.export_duration_ms <= 0:
            self.export_progress.setRange(0, 0)
        else:
            self.export_progress.setRange(0, 100)

        self.export_proc.readyReadStandardOutput.connect(self._on_export_stdout)
        self.export_proc.finished.connect(self._on_export_finished)

        self.export_proc.start()
        if not self.export_proc.waitForStarted(1500):
            if self.export_progress is not None:
                self.export_progress.close()
                self.export_progress = None
            QMessageBox.critical(self, "ffmpeg not found", "ffmpeg wasn't found on PATH.")
            self.export_proc = None
            self.export_out_path = out_path
            self.export_duration_ms = self.get_duration_ms(video)
            self.export_progress_buf = ""  # reset per export


def main() -> int:
    app = QApplication(sys.argv)
    set_dark_palette(app)

    w = LookLab()
    w.resize(860, 520)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

