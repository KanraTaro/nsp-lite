#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Sequence

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

from Core.Video.export import ExportOptions, build_export_args
from Core.Video.probe import get_duration_ms
from Core.Video.ffmpeg_exec import require_ffmpeg, require_ffplay
from Core.Video.filters import compose_vf

from Core.NSPL.Proc.adapters.ffmpeg import FfmpegAdapter, FfmpegAdapterConfig
from Core.NSPL.Proc.records import ProcRecordType
from Core.NSPL.Proc.runner import ProcessRunner
from Core.NSPL.Proc.sinks import CallbackSink


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


def build_look_vf(p: LookParams) -> str:
    """
    Builds ONLY the "look" portion of the vf chain.
    Scaling and format are handled by Core.Video.compose_vf so LookLab stays dumb.
    """
    parts: list[str] = []

    # Basic grade
    parts.append(
        f"eq=contrast={p.contrast:.3f}:"
        f"brightness={p.brightness:.3f}:"
        f"saturation={p.saturation:.3f}:"
        f"gamma={p.gamma:.3f}"
    )

    # Warmth: use colortemperature (primary) + colorbalance (punch assist)
    if abs(p.warmth) > 1e-4:
        # Map -1..+1 to Kelvin shift. 6500K is "neutral daylight".
        # This range is intentionally loud so you can actually see it.
        base_k = 6500.0
        kelvin_shift = 3500.0 * p.warmth   # -> 3000K .. 10000K-ish
        kelvin = max(1000.0, min(40000.0, base_k + kelvin_shift))
        parts.append(f"colortemperature=temperature={kelvin:.1f}")

        # Punch assist: subtle red/blue bias on top of temperature
        rs = max(-0.50, min(0.50, 0.30 * p.warmth))
        bs = max(-0.50, min(0.50, -0.28 * p.warmth))
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

        # NSPL Proc runner for ffplay preview (ignore records for now)
        self._proc_runner = ProcessRunner(CallbackSink(lambda _rec: None))
        self.preview_handle = None

        # Export state
        self.export_proc: QProcess | None = None
        self.export_progress: QProgressDialog | None = None
        self.export_duration_ms: int = 0
        self.export_out_path: str = ""

        # Ffmpeg progress adapter
        self._ffmpeg_adapter: FfmpegAdapter | None = None

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

        # Filter string display (final vf string, including scale + format)
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
        export_btn = QPushButton("Export Video")
        export_btn.clicked.connect(self.export_video)

        btns.addWidget(preview_btn)
        btns.addWidget(stop_btn)
        btns.addWidget(copy_btn)
        btns.addWidget(save_btn)
        btns.addWidget(export_btn)
        root.addLayout(btns)

        self.setLayout(root)

        # Update filter string when values change (slider + spinbox!)
        for row in [
            self.contrast, self.saturation, self.brightness, self.gamma,
            self.unsharp_luma, self.vignette, self.warmth, self.grain
        ]:
            row.slider.valueChanged.connect(self.update_filter)
            row.spin.valueChanged.connect(self.update_filter)

        self.scale_combo.currentIndexChanged.connect(self.update_filter)

        self.update_filter()

    def closeEvent(self, event) -> None:
        # Kill ffplay if user closes the window
        try:
            self.stop_preview()
        except Exception:
            pass
        super().closeEvent(event)

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
        )

    def _scale_width(self) -> int:
        return int(self.scale_combo.currentData() or 0)

    def update_filter(self) -> None:
        look_vf = build_look_vf(self.get_params())
        vf = compose_vf(
            look_vf=look_vf,
            fit_vf=None,
            scale_width=self._scale_width() if self._scale_width() > 0 else None,
            force_yuv420p=True,
        )
        self.filter_edit.setText(vf)

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

        try:
            ffplay = require_ffplay()
        except Exception as ex:
            QMessageBox.critical(self, "ffplay missing", str(ex))
            return

        vf = self.filter_edit.text().strip()
        cmd = [ffplay.path, "-loop", "0", "-vf", vf, video]

        self.stop_preview()

        try:
            self.preview_handle = self._proc_runner.spawn(
                cmd=cmd,
                tool="ffplay",
                cwd=None,
                env=None,
            )
        except Exception as ex:
            QMessageBox.critical(self, "Preview failed", str(ex))
            self.preview_handle = None

    def stop_preview(self) -> None:
        if self.preview_handle is not None:
            try:
                self._proc_runner.terminate(self.preview_handle, kill_after_sec=0.5)
            except Exception:
                pass
        self.preview_handle = None

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
                # Save ONLY the look vf (not the auto scale/format wrapper)
                look_vf = build_look_vf(self.get_params()).strip()
                f.write(look_vf + "\n")
        except Exception as ex:
            QMessageBox.critical(self, "Save failed", str(ex))

    # -------------------------
    # Export (async + percent)
    # -------------------------

    def _cancel_export(self) -> None:
        if self.export_proc is not None:
            self.export_proc.kill()

    def _on_export_stdout(self) -> None:
        if self.export_proc is None or self.export_progress is None or self._ffmpeg_adapter is None:
            return

        chunk = bytes(self.export_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not chunk:
            return

        # Ffmpeg -progress output is line-based key=value. Feed the adapter line by line.
        for raw_ln in chunk.splitlines():
            frags = self._ffmpeg_adapter.on_stdout_line(raw_ln)
            for frag in frags:
                if frag.type != ProcRecordType.PROGRESS:
                    continue

                pct = frag.data.get("pct", None)
                if pct is None:
                    continue

                try:
                    self.export_progress.setValue(int(pct))
                except Exception:
                    pass

    def _on_export_finished(self, exit_code: int, _status) -> None:
        if self.export_progress is not None:
            if exit_code == 0:
                try:
                    self.export_progress.setValue(100)
                except Exception:
                    pass
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
        self._ffmpeg_adapter = None

    def export_video(self) -> None:
        video = self.path_edit.text().strip()
        if not video:
            QMessageBox.warning(self, "No video", "Pick a video first.")
            return
        if not os.path.exists(video):
            QMessageBox.warning(self, "Missing file", f"File not found:\n{video}")
            return

        try:
            ffmpeg = require_ffmpeg()
        except Exception as ex:
            QMessageBox.critical(self, "ffmpeg missing", str(ex))
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

        # Duration goes through Core.Video (which goes through Deps + ffprobe)
        self.export_duration_ms = int(get_duration_ms(video) or 0)

        look_vf = build_look_vf(self.get_params()).strip()
        scale_width = self._scale_width()
        scale_width_opt = scale_width if scale_width > 0 else None

        export_opts = ExportOptions(
            input_path=video,
            output_path=out_path,
            vf=look_vf,
            preset="hq",
            scale_width=scale_width_opt,
            target=None,
            fit="pad",
        )
        args = build_export_args(export_opts)

        # Insert progress flags so adapter can work
        args2: list[str] = []
        i = 0
        while i < len(args):
            args2.append(args[i])
            if args[i] == "-nostats":
                args2.extend(["-progress", "pipe:1"])
            i += 1

        self._ffmpeg_adapter = FfmpegAdapter(FfmpegAdapterConfig(duration_ms=self.export_duration_ms))

        self.export_proc = QProcess(self)
        self.export_proc.setProgram(ffmpeg.path)
        self.export_proc.setArguments(args2)
        self.export_proc.setProcessChannelMode(QProcess.SeparateChannels)

        self.export_progress = QProgressDialog("Exporting...", "Cancel", 0, 100, self)
        self.export_progress.setWindowTitle("LookLab Export")
        self.export_progress.setMinimumDuration(0)
        self.export_progress.setValue(0)
        self.export_progress.canceled.connect(self._cancel_export)

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
            QMessageBox.critical(self, "ffmpeg failed", "ffmpeg could not be started.")
            self.export_proc = None
            self.export_out_path = ""
            self.export_duration_ms = 0
            self._ffmpeg_adapter = None


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    app = QApplication([sys.argv[0], *list(argv)])
    set_dark_palette(app)

    w = LookLab()
    w.resize(860, 520)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

