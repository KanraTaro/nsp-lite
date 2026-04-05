#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

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
    QTabWidget,
    QSpinBox,
)

from Core.Video.export import ExportOptions, build_export_args
from Core.Video.probe import get_duration_ms
from Core.Video.ffmpeg_exec import require_ffmpeg, require_ffplay
from Core.Video.filters import compose_vf
from Core.Video.frames_to_video import (
    FramesToVideoOptions,
    PreparedFramesToVideo,
    prepare_frames_to_video,
)

from Core.NSPL.Proc.adapters.ffmpeg import FfmpegAdapter, FfmpegAdapterConfig
from Core.NSPL.Proc.records import ProcRecordType
from Core.NSPL.Proc.runner import ProcessRunner
from Core.NSPL.Proc.sinks import CallbackSink


@dataclass
class LookParams:
    contrast: float = 1.0
    saturation: float = 1.0
    brightness: float = 0.0
    gamma: float = 1.0
    unsharp_luma: float = 0.0
    vignette: float = 0.0
    warmth: float = 0.0
    grain: float = 0.0


def build_look_vf(params: LookParams) -> str:
    parts: list[str] = []

    # Warmth first so the later eq pass does not visually flatten it as much.
    if abs(params.warmth) > 1e-4:
        base_kelvin: float = 6500.0
        kelvin_shift: float = 3500.0 * params.warmth
        kelvin: float = max(1000.0, min(40000.0, base_kelvin + kelvin_shift))
        parts.append(f"colortemperature=temperature={kelvin:.1f}")

        red_shift: float = max(-0.50, min(0.50, 0.30 * params.warmth))
        blue_shift: float = max(-0.50, min(0.50, -0.28 * params.warmth))
        parts.append(f"colorbalance=rs={red_shift:.3f}:bs={blue_shift:.3f}")

    parts.append(
        f"eq=contrast={params.contrast:.3f}:"
        f"brightness={params.brightness:.3f}:"
        f"saturation={params.saturation:.3f}:"
        f"gamma={params.gamma:.3f}"
    )

    if params.unsharp_luma > 1e-4:
        parts.append(f"unsharp=5:5:{params.unsharp_luma:.3f}:5:5:0.000")

    if params.vignette > 1e-4:
        angle: float = 0.2 + (params.vignette * 1.2)
        parts.append(f"vignette=PI/{1.0 / angle:.3f}")

    if params.grain > 1e-4:
        strength: float = max(0.0, min(12.0, params.grain * 12.0))
        parts.append(f"noise=alls={strength:.2f}:allf=t+u")

    return ",".join(parts)


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

        self._min: float = float(min_val)
        self._max: float = float(max_val)
        self._step: float = float(step)
        self._decimals: int = int(decimals)
        self._sync_guard: bool = False

        ticks: int = int(round((self._max - self._min) / self._step))
        self._ticks: int = ticks if ticks > 0 else 1

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

    def _on_slider(self, tick: int) -> None:
        if self._sync_guard:
            return

        self._sync_guard = True
        value: float = self._min + (tick * self._step)
        value = max(self._min, min(self._max, value))
        self.spin.setValue(value)
        self._sync_guard = False

    def _on_spin(self, value: float) -> None:
        if self._sync_guard:
            return

        self._sync_guard = True
        clamped: float = max(self._min, min(self._max, float(value)))
        tick: int = int(round((clamped - self._min) / self._step))
        self.slider.setValue(tick)
        self._sync_guard = False

    def value(self) -> float:
        return float(self.spin.value())

    def set_value(self, value: float) -> None:
        self.spin.setValue(float(value))


class FramesTab(QWidget):
    def __init__(self, *, on_built_video: Callable[[str], None]) -> None:
        super().__init__()
        self._on_built_video = on_built_video

        self.build_proc: QProcess | None = None
        self.build_progress: QProgressDialog | None = None
        self._ffmpeg_adapter: FfmpegAdapter | None = None
        self._prep: PreparedFramesToVideo | None = None
        self._out_path: str = ""

        root = QVBoxLayout()

        dir_row = QHBoxLayout()
        self.frames_dir_edit = QLineEdit()
        self.frames_dir_edit.setPlaceholderText("Pick a folder containing frames, like 0001.png ...")
        dir_browse_btn = QPushButton("Browse")
        dir_browse_btn.clicked.connect(self.browse_frames_dir)
        dir_row.addWidget(QLabel("Frames dir:"))
        dir_row.addWidget(self.frames_dir_edit, 1)
        dir_row.addWidget(dir_browse_btn)
        root.addLayout(dir_row)

        opts_row = QHBoxLayout()

        self.pattern_edit = QLineEdit("*.png")
        self.pattern_edit.setMinimumWidth(120)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(12)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("PingPong", "pingpong")
        self.mode_combo.addItem("Forward", "forward")

        opts_row.addWidget(QLabel("Pattern:"))
        opts_row.addWidget(self.pattern_edit)
        opts_row.addSpacing(10)
        opts_row.addWidget(QLabel("FPS:"))
        opts_row.addWidget(self.fps_spin)
        opts_row.addSpacing(10)
        opts_row.addWidget(QLabel("Mode:"))
        opts_row.addWidget(self.mode_combo, 1)
        root.addLayout(opts_row)

        out_row = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Output mp4 path")
        out_browse_btn = QPushButton("Save As")
        out_browse_btn.clicked.connect(self.browse_out_path)
        out_row.addWidget(QLabel("Output:"))
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(out_browse_btn)
        root.addLayout(out_row)

        btn_row = QHBoxLayout()
        build_btn = QPushButton("Build Video")
        build_btn.clicked.connect(self.build_video)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._cancel_build)
        btn_row.addWidget(build_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        note = QLabel("Tip: Build the loop here, then switch to Grade tab to color grade and export.")
        note.setWordWrap(True)
        root.addWidget(note)

        self.setLayout(root)

    def browse_frames_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select frames directory",
            os.path.expanduser("~"),
        )
        if path:
            self.frames_dir_edit.setText(path)
            if self.out_edit.text().strip() == "":
                self.out_edit.setText(os.path.join(path, "pingpong.mp4"))

    def browse_out_path(self) -> None:
        frames_dir: str = self.frames_dir_edit.text().strip()
        start_dir: str = frames_dir if frames_dir != "" else os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save output video",
            os.path.join(start_dir, "pingpong.mp4"),
            "MP4 Video (*.mp4);;All Files (*)",
        )
        if path:
            self.out_edit.setText(path)

    def _cancel_build(self) -> None:
        if self.build_proc is not None:
            try:
                self.build_proc.kill()
            except Exception:
                pass

    def _on_build_stdout(self) -> None:
        if self.build_proc is None or self.build_progress is None or self._ffmpeg_adapter is None:
            return

        chunk = bytes(self.build_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if chunk == "":
            return

        for raw_line in chunk.splitlines():
            fragments = self._ffmpeg_adapter.on_stdout_line(raw_line)
            for fragment in fragments:
                if fragment.type != ProcRecordType.PROGRESS:
                    continue

                pct = fragment.data.get("pct", None)
                if pct is None:
                    continue

                try:
                    self.build_progress.setValue(int(pct))
                except Exception:
                    pass

    def _on_build_finished(self, exit_code: int, _status) -> None:
        if self.build_progress is not None:
            if exit_code == 0:
                try:
                    self.build_progress.setValue(100)
                except Exception:
                    pass
            self.build_progress.close()
            self.build_progress = None

        if self._prep is not None:
            try:
                self._prep.cleanup()
            except Exception:
                pass
            self._prep = None

        if exit_code == 0:
            QMessageBox.information(self, "Build complete", f"Wrote:\n{self._out_path}")
            try:
                self._on_built_video(self._out_path)
            except Exception:
                pass
        else:
            err: str = ""
            if self.build_proc is not None:
                err = bytes(self.build_proc.readAllStandardError()).decode("utf-8", errors="replace")
            if err.strip() == "":
                err = "ffmpeg exited with a non-zero code."
            QMessageBox.critical(self, "Build failed", err.strip())

        self.build_proc = None
        self._out_path = ""
        self._ffmpeg_adapter = None

    def build_video(self) -> None:
        frames_dir: str = self.frames_dir_edit.text().strip()
        if frames_dir == "":
            QMessageBox.warning(self, "No frames dir", "Pick a frames directory first.")
            return
        if not os.path.isdir(frames_dir):
            QMessageBox.warning(self, "Missing dir", f"Directory not found:\n{frames_dir}")
            return

        out_path: str = self.out_edit.text().strip()
        if out_path == "":
            out_path = os.path.join(frames_dir, "pingpong.mp4")
            self.out_edit.setText(out_path)

        pattern: str = self.pattern_edit.text().strip() or "*.png"
        fps: int = int(self.fps_spin.value())
        mode: str = str(self.mode_combo.currentData() or "pingpong")

        try:
            ffmpeg = require_ffmpeg()
        except Exception as ex:
            QMessageBox.critical(self, "ffmpeg missing", str(ex))
            return

        if self.build_proc is not None:
            try:
                self.build_proc.kill()
            except Exception:
                pass
            self.build_proc = None

        opts = FramesToVideoOptions(
            frames_dir=frames_dir,
            output_path=out_path,
            fps=fps,
            pattern=pattern,
            mode=mode,
            include_progress=True,
        )

        try:
            self._prep = prepare_frames_to_video(opts)
        except Exception as ex:
            QMessageBox.critical(self, "Build setup failed", str(ex))
            self._prep = None
            return

        self._out_path = out_path
        self._ffmpeg_adapter = FfmpegAdapter(
            FfmpegAdapterConfig(duration_ms=int(self._prep.duration_ms))
        )

        self.build_proc = QProcess(self)
        self.build_proc.setProgram(ffmpeg.path)
        self.build_proc.setArguments(self._prep.args)
        self.build_proc.setProcessChannelMode(QProcess.SeparateChannels)

        self.build_progress = QProgressDialog("Building video from frames...", "Cancel", 0, 100, self)
        self.build_progress.setWindowTitle("LookLab Frames Build")
        self.build_progress.setMinimumDuration(0)
        self.build_progress.setValue(0)
        self.build_progress.canceled.connect(self._cancel_build)

        if self._prep.duration_ms <= 0:
            self.build_progress.setRange(0, 0)
        else:
            self.build_progress.setRange(0, 100)

        self.build_proc.readyReadStandardOutput.connect(self._on_build_stdout)
        self.build_proc.finished.connect(self._on_build_finished)

        self.build_proc.start()
        if not self.build_proc.waitForStarted(1500):
            if self.build_progress is not None:
                self.build_progress.close()
                self.build_progress = None

            QMessageBox.critical(self, "ffmpeg failed", "ffmpeg could not be started.")
            self.build_proc = None

            if self._prep is not None:
                try:
                    self._prep.cleanup()
                except Exception:
                    pass
                self._prep = None

            self._out_path = ""
            self._ffmpeg_adapter = None


class GradeTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._proc_runner = ProcessRunner(CallbackSink(lambda _rec: None))
        self.preview_handle = None

        self.export_proc: QProcess | None = None
        self.export_progress: QProgressDialog | None = None
        self.export_duration_ms: int = 0
        self.export_out_path: str = ""
        self._ffmpeg_adapter: FfmpegAdapter | None = None

        root = QVBoxLayout()

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Pick a video (ideally a 1–3s preview clip)")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_video)
        path_row.addWidget(QLabel("Video:"))
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        root.addLayout(path_row)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale width:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItem("Original", 0)
        self.scale_combo.addItem("1080p wide (1920)", 1920)
        self.scale_combo.addItem("1440p wide (2560)", 2560)
        self.scale_combo.addItem("4K wide (3840)", 3840)
        scale_row.addWidget(self.scale_combo, 1)
        root.addLayout(scale_row)

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

        self.filter_edit = QLineEdit()
        self.filter_edit.setReadOnly(True)
        root.addWidget(QLabel("Generated -vf filtergraph:"))
        root.addWidget(self.filter_edit)

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

        watched_rows = [
            self.contrast,
            self.saturation,
            self.brightness,
            self.gamma,
            self.unsharp_luma,
            self.vignette,
            self.warmth,
            self.grain,
        ]
        for row in watched_rows:
            row.slider.valueChanged.connect(self.update_filter)
            row.spin.valueChanged.connect(self.update_filter)

        self.scale_combo.currentIndexChanged.connect(self.update_filter)
        self.update_filter()

    def closeEvent(self, event) -> None:
        try:
            self.stop_preview()
        except Exception:
            pass
        super().closeEvent(event)

    def set_video_path(self, path: str) -> None:
        self.path_edit.setText(path.strip())

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
        look_vf: str = build_look_vf(self.get_params())
        vf: str = compose_vf(
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
        video: str = self.path_edit.text().strip()
        if video == "":
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

        vf: str = self.filter_edit.text().strip()
        cmd: list[str] = [ffplay.path, "-loop", "0", "-vf", vf, video]

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
        default_name: str = "look_01.fffilter"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save preset",
            default_name,
            "FFmpeg Filter (*.fffilter);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as handle:
                look_vf: str = build_look_vf(self.get_params()).strip()
                handle.write(look_vf + "\n")
        except Exception as ex:
            QMessageBox.critical(self, "Save failed", str(ex))

    def _cancel_export(self) -> None:
        if self.export_proc is not None:
            self.export_proc.kill()

    def _on_export_stdout(self) -> None:
        if self.export_proc is None or self.export_progress is None or self._ffmpeg_adapter is None:
            return

        chunk = bytes(self.export_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        if chunk == "":
            return

        for raw_line in chunk.splitlines():
            fragments = self._ffmpeg_adapter.on_stdout_line(raw_line)
            for fragment in fragments:
                if fragment.type != ProcRecordType.PROGRESS:
                    continue

                pct = fragment.data.get("pct", None)
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
            err: str = ""
            if self.export_proc is not None:
                err = bytes(self.export_proc.readAllStandardError()).decode("utf-8", errors="replace")
            if err.strip() == "":
                err = "ffmpeg exited with a non-zero code."
            QMessageBox.critical(self, "Export failed", err.strip())

        self.export_proc = None
        self.export_out_path = ""
        self.export_duration_ms = 0
        self._ffmpeg_adapter = None

    def export_video(self) -> None:
        video: str = self.path_edit.text().strip()
        if video == "":
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

        if self.export_proc is not None:
            try:
                self.export_proc.kill()
            except Exception:
                pass
            self.export_proc = None

        self.export_out_path = out_path
        self.export_duration_ms = int(get_duration_ms(video) or 0)

        look_vf: str = build_look_vf(self.get_params()).strip()
        scale_width: int = self._scale_width()
        scale_width_opt: int | None = scale_width if scale_width > 0 else None

        export_opts = ExportOptions(
            input_path=video,
            output_path=out_path,
            vf=look_vf,
            preset="hq",
            scale_width=scale_width_opt,
            target=None,
            fit="pad",
        )
        args: list[str] = build_export_args(export_opts)

        args_with_progress: list[str] = []
        for arg in args:
            args_with_progress.append(arg)
            if arg == "-nostats":
                args_with_progress.extend(["-progress", "pipe:1"])

        self._ffmpeg_adapter = FfmpegAdapter(
            FfmpegAdapterConfig(duration_ms=self.export_duration_ms)
        )

        self.export_proc = QProcess(self)
        self.export_proc.setProgram(ffmpeg.path)
        self.export_proc.setArguments(args_with_progress)
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


class LookLab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LookLab")

        root = QVBoxLayout()

        self.tabs = QTabWidget()
        self.grade_tab = GradeTab()
        self.frames_tab = FramesTab(on_built_video=self._on_built_video)

        self.tabs.addTab(self.frames_tab, "Frames")
        self.tabs.addTab(self.grade_tab, "Grade")

        root.addWidget(self.tabs)
        self.setLayout(root)

    def _on_built_video(self, out_path: str) -> None:
        self.grade_tab.set_video_path(out_path)
        self.tabs.setCurrentWidget(self.grade_tab)

    def closeEvent(self, event) -> None:
        try:
            self.grade_tab.stop_preview()
        except Exception:
            pass
        super().closeEvent(event)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    app = QApplication([sys.argv[0], *list(argv)])
    set_dark_palette(app)

    window = LookLab()
    window.resize(900, 600)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
