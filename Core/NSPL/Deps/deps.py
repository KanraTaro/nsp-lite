from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple


class DependencyError(RuntimeError):
    def __init__(self, message: str, *, exe_name: str, hints: str) -> None:
        super().__init__(message)
        self.exe_name: str = exe_name
        self.hints: str = hints


@dataclass(frozen=True)
class ExecutableInfo:
    name: str
    path: str
    version: str


def which(exe_name: str) -> Optional[str]:
    """
    Cross-platform PATH lookup. Returns absolute path if found, otherwise None.
    """
    found: Optional[str] = shutil.which(exe_name)
    if found is None:
        return None
    return os.path.abspath(found)


def _candidate_paths_from_env(env_vars: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for key in env_vars:
        raw: Optional[str] = os.environ.get(key)
        if raw is None:
            continue
        value: str = raw.strip()
        if value == "":
            continue
        paths.append(value)
    return paths


def find_executable(exe_name: str, *, env_vars: Sequence[str] = ()) -> Optional[str]:
    """
    Find an executable via:
    1) explicit env var override(s)
    2) PATH lookup
    Returns absolute path or None.
    """
    # 1) Env override(s)
    candidates: list[str] = _candidate_paths_from_env(env_vars)
    for candidate in candidates:
        # If user gives a directory, try appending the exe_name
        if os.path.isdir(candidate):
            joined: str = os.path.join(candidate, exe_name)
            path_guess: Optional[str] = which(joined) or (os.path.abspath(joined) if os.path.exists(joined) else None)
            if path_guess is not None and os.access(path_guess, os.X_OK):
                return os.path.abspath(path_guess)

        # If user gives a full path, accept if it exists
        if os.path.exists(candidate):
            abs_path: str = os.path.abspath(candidate)
            if os.access(abs_path, os.X_OK) or abs_path.lower().endswith(".exe"):
                return abs_path

        # Otherwise, try resolving via PATH semantics (handles "ffmpeg.exe" too)
        resolved: Optional[str] = which(candidate)
        if resolved is not None:
            return resolved

    # 2) PATH
    return which(exe_name)


def verify_executable(path: str, *, verify_args: Sequence[str] = ("-version",), timeout_sec: float = 3.0) -> Tuple[bool, str]:
    """
    Run `<path> <verify_args>` and return (ok, version_string_or_error_snippet).
    """
    try:
        proc = subprocess.run(
            [path, *verify_args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except FileNotFoundError:
        return False, "Executable not found."
    except PermissionError:
        return False, "Permission denied running executable."
    except subprocess.TimeoutExpired:
        return False, f"Timed out running: {os.path.basename(path)} {' '.join(verify_args)}"
    except Exception as ex:
        return False, f"Failed running executable: {ex}"

    out: str = (proc.stdout or "").strip()
    err: str = (proc.stderr or "").strip()
    combined: str = (out + "\n" + err).strip()

    # We treat exit 0 as "ok". Some tools exit non-zero but still print version text,
    # but for dependency sanity we want a strong signal.
    if proc.returncode != 0:
        snippet: str = combined[:400] if combined else f"Exit code {proc.returncode}."
        return False, snippet

    snippet_ok: str = combined[:400] if combined else "OK"
    return True, snippet_ok


def require_executable(
    exe_name: str,
    *,
    env_vars: Sequence[str] = (),
    verify_args: Sequence[str] = ("-version",),
    install_hints: str = "",
) -> ExecutableInfo:
    """
    Find + verify an executable. Raises DependencyError on failure.
    """
    path: Optional[str] = find_executable(exe_name, env_vars=env_vars)
    if path is None:
        hints: str = install_hints.strip()
        message: str = (
            f"Missing dependency: '{exe_name}'.\n"
            f"Checked PATH"
            + (f" and env vars: {', '.join(env_vars)}" if env_vars else "")
            + ".\n"
            + (hints if hints else "")
        ).strip()
        raise DependencyError(message, exe_name=exe_name, hints=hints)

    ok, info = verify_executable(path, verify_args=verify_args)
    if not ok:
        hints = install_hints.strip()
        message = (
            f"Dependency check failed for '{exe_name}'.\n"
            f"Resolved path: {path}\n"
            f"Verify args: {' '.join(verify_args)}\n"
            f"Error:\n{info}\n"
            + (("\n" + hints) if hints else "")
        ).strip()
        raise DependencyError(message, exe_name=exe_name, hints=hints)

    return ExecutableInfo(name=exe_name, path=path, version=info)


def ffmpeg_install_hints() -> str:
    """
    Human-friendly install hints. Does not attempt installation.
    """
    system: str = platform.system().lower()

    if "windows" in system:
        return (
            "Install FFmpeg on Windows (one option):\n"
            "  winget install Gyan.FFmpeg\n"
            "\n"
            "Then ensure ffmpeg.exe and ffplay.exe are on PATH, or set:\n"
            "  NSP_FFMPEG=C:\\path\\to\\ffmpeg.exe\n"
            "  NSP_FFPLAY=C:\\path\\to\\ffplay.exe"
        )

    if "darwin" in system or "mac" in system:
        return (
            "Install FFmpeg on macOS:\n"
            "  brew install ffmpeg\n"
            "\n"
            "Or set env overrides:\n"
            "  NSP_FFMPEG=/path/to/ffmpeg\n"
            "  NSP_FFPLAY=/path/to/ffplay"
        )

    # Assume Linux / Unix
    return (
        "Install FFmpeg on Linux (pick the one that matches your distro):\n"
        "  Debian/Ubuntu: sudo apt install ffmpeg\n"
        "  Fedora:        sudo dnf install ffmpeg\n"
        "  Arch:          sudo pacman -S ffmpeg\n"
        "\n"
        "Or set env overrides:\n"
        "  NSP_FFMPEG=/path/to/ffmpeg\n"
        "  NSP_FFPLAY=/path/to/ffplay"
    )

