# LookLab

LookLab is the first working NSPL GUI example for the Video domain.

It currently provides two focused workflows:

* **Frames**
  Build a video clip from an ordered frame folder, including ping-pong loop creation.

* **Grade**
  Preview, tweak, save, and export FFmpeg-based look adjustments for an existing video.

This GUI exists to prove out a full vertical slice of the NSPL stack:

* GUI discovery through `GUICLI`
* dependency verification through `Core.NSPL.Deps`
* video process execution through FFmpeg
* progress parsing through `Core.NSPL.Proc.adapters.ffmpeg`
* reusable video logic under `Core/Video`

---

## Current architecture

LookLab currently uses a **GUI → Core** model.

That means `launch.py` calls reusable Core modules directly, including:

* `Core.Video.frames_to_video`
* `Core.Video.export`
* `Core.Video.probe`
* `Core.Video.filters`
* `Core.Video.ffmpeg_exec`

It also uses `Core.NSPL.Proc` for local process handling and FFmpeg progress parsing inside the GUI.

### Important note

LookLab does **not yet** call Video Skills through `SkillCLI`.

So while the underlying Video domain now has proper Skills, this GUI is still directly consuming Core logic rather than acting as a thin shell over Skill entrypoints.

That is acceptable for the current milestone, but it is **not the final intended NSPL pattern**.

---

## Why LookLab still matters

Even in its current form, LookLab is an important reference implementation because it proves:

* NSPL GUI discovery works
* NSPL alias / launcher flow works
* FFmpeg dependency checks work
* QProcess-driven progress bars work
* frame building and grading can be chained in one tool
* a generated clip can immediately flow into the grading tab

This makes LookLab the first truly usable NSPL GUI pipeline in the repo.

---

## Tabs

## Frames

The Frames tab builds a video from an image sequence.

Supported modes currently include:

* `forward`
* `pingpong`

The Frames tab currently uses `Core.Video.frames_to_video.prepare_frames_to_video(...)` to:

* collect and validate frames
* construct the playback sequence
* generate a concat file
* prepare FFmpeg arguments
* estimate duration for progress UI
* provide cleanup hooks

The GUI then launches FFmpeg with `QProcess` and uses the Proc FFmpeg adapter to convert `-progress pipe:1` output into percent updates.

## Grade

The Grade tab provides:

* look controls
* ffplay preview
* preset saving to `.fffilter`
* export to final video

It currently uses:

* `build_look_vf(...)` in `launch.py`
* `Core.Video.filters.compose_vf(...)`
* `Core.Video.export.build_export_args(...)`
* `Core.Video.probe.get_duration_ms(...)`

Preview is handled via `ffplay`, and export is handled via `ffmpeg`.

---

## Relationship to Skills

The Video domain now includes Skills such as:

* `Video.Frames.BuildVideo`
* `Video.Frames.PingPong`
* `Video.Clip.Export`

These are the canonical CLI and agent-facing entrypoints.

Right now, LookLab does **not** invoke those Skills. Instead, both LookLab and the Skills share the same Core layer.

That means the architecture is currently:

* **Skills → Core**
* **GUI → Core**

The long-term target is:

* **Skills → Core**
* **GUI → Skills** where practical, or at minimum a thinner GUI layer that mirrors Skill behavior exactly

---

## Proc status

LookLab currently uses Proc in a partial but useful way:

* it uses the FFmpeg Proc adapter for progress parsing
* it uses `ProcessRunner` for preview process handling
* it does **not yet** route all video execution through a fully unified Proc-driven path across GUI, terminal, agent, and future web interfaces

### Long-term Proc goal

The intended direction is for process-driving features to become more uniform so that:

* terminal usage can show progress
* GUI usage can show progress
* web usage can show progress
* agent / Roh usage can observe progress through the same sink model

That likely means pushing more progress-aware process execution into shared Core and/or shared Skill-level execution paths, instead of letting each frontend solve that separately.

This is an architectural follow-up, not a blocker.

---

## Known refactors planned

## 1. GUI shell thinning

`launch.py` is still carrying too much application logic.

Over time, LookLab should move toward being a thinner shell that focuses on:

* layout
* user interaction
* progress display
* tab coordination
* file selection

while more execution behavior lives in shared Core and/or Skill entrypoints.

## 2. Skill alignment

LookLab should eventually align more tightly with Video Skills so that features available to the user are also available to agents and automation through the same stable entrypoints.

This is important because NSPL is not being designed for manual-only tools. Manual tools are expected to become usable by Roh, agents, workers, and web frontends later.

## 3. Proc unification

Proc should become a more authoritative execution layer for FFmpeg-driven workflows, so progress reporting and cancellation behavior are not split across frontends.

## 4. Web frontend path

LookLab currently proves the desktop GUI lane, but the same underlying Video domain should later support a web-facing frontend as well.

That future web lane should reuse the same Core and Skill surfaces rather than re-implementing behavior.

---

## Why this tool exists

LookLab is both:

* a usable video utility
* a systems test for NSPL architecture

It helped validate:

* `GUICLI`
* launcher flow
* dependency verification
* Video Core extraction
* Skill separation
* process progress UI
* front-to-back workflow chaining

Because of that, LookLab is more important than a normal one-off tool. It is one of the first real examples of how NSPL applications can feel when the pipeline is working correctly.

---

## Launch

Typical invocation is through GUICLI:

`python -m Core.NSPL.GUICLI run Video.LookLab`

Or through your NSPL launcher / alias layer if configured.

---

## Design stance

LookLab is considered a **working milestone**, not the final architectural form.

That means:

* it is valid to use now
* it is worth keeping stable
* it is also expected to be refactored toward thinner GUI behavior and stronger Skill / Proc alignment over time
