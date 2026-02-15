## `Core/NSPL/Deps/README.md`

Per your preference: plain markdown, no code fences needed. Keep it short and functional.

Core/NSPL/Deps

This module provides a small, reusable dependency discovery + verification primitive for NSP Lite.

What it does

* Finds executables via PATH
* Supports explicit env var overrides (ex: NSP_FFMPEG, NSP_FFPLAY)
* Verifies executables by running a version command (default: -version)
* Returns actionable install hints on failure (does not auto-install)

Why it exists
Skills should stay boring. When multiple skills need “check tool X exists”, that logic belongs in Core so it’s tested once and reused everywhere.

Primary API

* which(exe_name) -> absolute path or None
* find_executable(exe_name, env_vars=[...]) -> absolute path or None
* verify_executable(path, verify_args=["-version"]) -> (ok, version_or_error_snippet)
* require_executable(exe_name, env_vars=[...], install_hints="...") -> ExecutableInfo or raises DependencyError

FFmpeg hints
Use ffmpeg_install_hints() to get platform-specific guidance without attempting installation.

