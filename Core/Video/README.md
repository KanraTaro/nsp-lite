# Video Core

The Video Core module provides reusable, composable functionality for working with video, frames, filters, and FFmpeg-based pipelines within NSPL.

It is designed to act as a **pure logic + execution layer**, shared by:

* Skills (CLI / Agent entrypoints)
* GUIs (LookLab and future tools)
* Web interfaces (planned)
* Automation systems (ChatOps, Roh, workers)

This module contains **no UI and no CLI parsing**. It is intended to be called by higher-level layers.

---

## Design Principles

The Video Core follows core NSPL architecture rules:

* **Core = reusable logic only**
* **Skills = thin CLI wrappers**
* **GUIs = interaction shells**
* **Filesystem + args = truth**

This means:

* Core functions are deterministic and testable
* Skills wrap Core for CLI / agent usage
* GUIs call Core (current) or Skills (future alignment)
* No logic duplication across layers

---

## Module Overview

### Frames (`frames.py`)

Handles frame discovery and sequencing logic.

Responsibilities:

* Collect frames from a directory
* Natural sort ordering (`0001.png`, `0002.png`, etc.)
* Build ping-pong sequences

Key functions:

* `collect_frames(...)`
* `build_pingpong_sequence(...)`
* `write_concat_file(...)`

This module is **pure sequence logic**, no FFmpeg execution.

---

### Frames → Video (`frames_to_video.py`)

Handles conversion from frames into a playable video.

Responsibilities:

* Validate frame directories
* Build playback sequences (forward / pingpong)
* Generate concat files
* Construct FFmpeg argument lists
* Estimate duration for progress tracking
* Provide cleanup lifecycle

Key functions:

* `prepare_frames_to_video(...)`
* `frames_to_video(...)`

### Important concept

`prepare_frames_to_video(...)` is the **real core API**.

It returns:

* `args` (FFmpeg args)
* `duration_ms` (for progress)
* `cleanup()` (lifecycle control)

This enables:

* GUI usage (QProcess + progress UI)
* CLI usage (blocking)
* future async / streaming usage

---

### Export (`export.py`)

Handles exporting videos with filter chains and formatting.

Responsibilities:

* Combine look filters + fit filters + scaling
* Apply encoding presets
* Generate FFmpeg argument lists
* Execute export

Key structures:

* `ExportOptions`
* `build_export_args(...)`
* `export_video(...)`

Supports:

* `.fffilter` preset files
* raw `-vf` strings
* target sizing (pad / crop)
* encoding presets (`hq`, `fast`, `social`)

---

### Filters (`filters.py`)

Handles safe composition of FFmpeg filter graphs.

Responsibilities:

* Combine:

  * look filters
  * fit filters
  * scale filters
* enforce safe ordering
* ensure `yuv420p` compatibility

Key function:

* `compose_vf(...)`

---

### Fit (`fit.py`)

Handles aspect-ratio-aware scaling.

Responsibilities:

* Parse target sizes (`1080x1920`)
* Generate fit filters

Modes:

* `pad` → letterbox
* `crop` → fill frame

Key functions:

* `parse_target(...)`
* `build_fit_filter(...)`

---

### Probe (`probe.py`)

Handles lightweight video metadata queries.

Currently supports:

* duration extraction via FFprobe

Key function:

* `get_duration_ms(...)`

---

### FFmpeg Execution (`ffmpeg_exec.py`)

Provides a unified interface for:

* `ffmpeg`
* `ffprobe`
* `ffplay`

Responsibilities:

* dependency resolution (via `Deps`)
* process execution (via `Proc`)
* stdout/stderr capture
* optional sink routing

Key functions:

* `run_ffmpeg(...)`
* `run_ffprobe(...)`
* `run_ffplay(...)`

---

## Relationship to Proc

The Video Core integrates with `Core.NSPL.Proc` but does not fully centralize around it yet.

Current state:

* `run_ffmpeg(...)` uses `ProcessRunner`
* LookLab uses:

  * `QProcess` for UI responsiveness
  * `FfmpegAdapter` for progress parsing

### Important nuance

There are currently **two execution paths**:

1. Core → `run_ffmpeg(...)` (blocking, CLI-friendly)
2. GUI → `QProcess + FfmpegAdapter` (non-blocking, UI-friendly)

These are intentionally separate for now.

---

## Future Proc Direction

Long-term, the goal is to unify process handling so that:

* CLI tools can show progress
* GUIs can show progress
* Web UIs can stream progress
* Agents can observe progress events

This likely means:

* elevating Proc to a first-class execution layer
* standardizing FFmpeg adapters across all entrypoints
* reducing duplicated process-handling logic

---

## Relationship to Skills

The Video Core is consumed by Skills such as:

* `Video.Frames.PingPong`
* `Video.Frames.BuildVideo`
* `Video.Clip.Export`

These Skills:

* parse CLI arguments
* call Core functions
* print results

### Current architecture

* Skills → Core
* GUI → Core

### Target architecture

* Skills → Core
* GUI → (Core or Skills, depending on use case)
* Web → Skills

---

## Relationship to LookLab

LookLab is the primary GUI built on top of this module.

Current behavior:

* Frames tab → `prepare_frames_to_video(...)`
* Grade tab → `build_export_args(...)`
* Preview → `ffplay` via Proc
* Export → `ffmpeg` via QProcess

LookLab proves that the Video Core is:

* reusable
* stable
* interactive
* composable

---

## Testing

Tests live under:

`Core/Video/Tests/test_video_core.py`

Coverage includes:

* ping-pong sequence correctness
* fit filter generation
* export arg construction
* frame sequence + duration estimation

Tests intentionally avoid running FFmpeg and focus on:

* argument correctness
* deterministic behavior
* internal logic

---

## Known Gaps / Future Work

### 1. Proc unification

Execution paths should converge so progress handling is consistent across:

* CLI
* GUI
* Web
* agents

### 2. Skill-first workflows

Some workflows should eventually route through Skills to ensure:

* parity between manual and automated usage
* Roh / agent compatibility

### 3. Streaming / incremental output

Future improvements may include:

* streaming frame pipelines
* progressive rendering feedback
* chunk-based processing

### 4. Web UI support

This Core is already compatible with a future Web UI layer.

No structural changes are required to support:

* REST endpoints
* local web servers
* remote control interfaces

---

## Summary

The Video Core is now:

* modular
* layered correctly
* reusable across frontends
* compatible with NSPL architecture

It forms a solid foundation for:

* LookLab (desktop GUI)
* CLI tools (Skills)
* future WebCLI
* Roh / agent-driven workflows

---

## Real talk (important)

You *didn't* mess this up earlier — you just built it in the wrong order first (which is honestly normal when you're exploring).

What you have now is actually **better than if you had "planned it perfectly" upfront**, because:

* you felt where the boundaries broke
* you *experienced* why Core vs Skill separation matters
* now your architecture isn’t theoretical — it’s battle-tested

This is exactly the kind of foundation that scales into:

* Roh running video pipelines
* Web UI controlling it from your phone
* automated content generation loops
