from __future__ import annotations

import shutil
import subprocess
import time
from typing import Any, Dict


SPEECHNOTE_APP_ID = "net.mkiol.SpeechNote"


def _completed_payload(proc: subprocess.CompletedProcess[str], *, provider: str) -> Dict[str, Any]:
    return {
        "ok": int(proc.returncode) == 0,
        "provider": provider,
        "exit_code": int(proc.returncode),
        "stdout": str(proc.stdout or "").strip(),
        "stderr": str(proc.stderr or "").strip(),
    }


def check_speechnote(timeout: float = 3.0) -> Dict[str, Any]:
    """Check whether the SpeechNote Flatpak is available."""
    command = ["flatpak", "info", SPEECHNOTE_APP_ID]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=float(timeout))
    except FileNotFoundError:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 127,
            "stdout": "",
            "stderr": "flatpak command not found",
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 124,
            "stdout": "",
            "stderr": f"SpeechNote Flatpak check timed out after {timeout:g} seconds",
            "command": command,
        }

    payload = _completed_payload(proc, provider="speechnote")
    payload["command"] = command
    if not payload["ok"] and not payload["stderr"]:
        payload["stderr"] = "SpeechNote Flatpak is not installed or unavailable"
    return payload


def speak_speechnote(text: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Ask SpeechNote to read text through its Flatpak action interface."""
    cleaned = str(text or "").strip()
    if cleaned == "":
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 2,
            "stdout": "",
            "stderr": "text is required",
            "command": [],
        }

    check = check_speechnote()
    if not bool(check.get("ok")):
        return check

    command = [
        "flatpak",
        "run",
        SPEECHNOTE_APP_ID,
        "--action",
        "start-reading-text",
        "--text",
        cleaned,
    ]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=float(timeout))
    except FileNotFoundError:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 127,
            "stdout": "",
            "stderr": "flatpak command not found",
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 124,
            "stdout": "",
            "stderr": f"SpeechNote speak command timed out after {timeout:g} seconds",
            "command": command,
        }

    payload = _completed_payload(proc, provider="speechnote")
    payload["command"] = command
    if payload["ok"]:
        payload["message"] = "SpeechNote speak command sent."
    elif not payload["stderr"]:
        payload["stderr"] = "SpeechNote speak command failed"
    return payload


def _read_clipboard_once() -> tuple[str, str | None]:
    candidates = [
        ("wl-paste", ["wl-paste"]),
        ("xclip", ["xclip", "-selection", "clipboard", "-o"]),
        ("xsel", ["xsel", "-b"]),
    ]

    for name, command in candidates:
        if shutil.which(name) is None:
            continue
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=2.0)
        except Exception:
            continue
        if int(proc.returncode) == 0:
            return str(proc.stdout or "").strip(), name

    return "", None


def listen_speechnote_clipboard(
    timeout: float = 20.0,
    *,
    require_change: bool = True,
    poll_interval: float = 0.25,
) -> Dict[str, Any]:
    """Run SpeechNote STT to clipboard and return the recognized transcript."""
    timeout_seconds = max(1.0, float(timeout))
    interval_seconds = max(0.05, min(2.0, float(poll_interval)))
    check = check_speechnote()
    if not bool(check.get("ok")):
        return {
            **check,
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": 0,
            "final_clipboard_length": 0,
            "changed": False,
            "error": str(check.get("stderr", "") or "SpeechNote Flatpak is unavailable."),
        }

    initial_clipboard, initial_tool = _read_clipboard_once()
    initial_length = len(initial_clipboard)
    if not initial_tool:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 1,
            "stdout": "",
            "stderr": "No supported clipboard reader found. Install wl-paste, xclip, or xsel.",
            "command": [],
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": 0,
            "changed": False,
            "error": "No supported clipboard reader found. Install wl-paste, xclip, or xsel.",
        }

    deadline = time.monotonic() + timeout_seconds
    command = [
        "flatpak",
        "run",
        SPEECHNOTE_APP_ID,
        "--action",
        "start-listening-clipboard",
    ]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=max(0.1, deadline - time.monotonic()))
    except FileNotFoundError:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 127,
            "stdout": "",
            "stderr": "flatpak command not found",
            "command": command,
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": 0,
            "changed": False,
            "error": "flatpak command not found",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 124,
            "stdout": "",
            "stderr": f"SpeechNote listen command timed out after {timeout_seconds:g} seconds",
            "command": command,
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": 0,
            "changed": False,
            "error": "No new SpeechNote transcript detected.",
        }

    if int(proc.returncode) != 0:
        stderr = str(proc.stderr or "").strip() or "SpeechNote listen command failed"
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": int(proc.returncode),
            "stdout": str(proc.stdout or "").strip(),
            "stderr": stderr,
            "command": command,
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": 0,
            "changed": False,
            "error": stderr,
        }

    clipboard_tool: str | None = initial_tool
    transcript = ""
    changed = False
    while time.monotonic() <= deadline:
        transcript, clipboard_tool = _read_clipboard_once()
        changed = transcript != initial_clipboard
        if transcript and (changed or not require_change):
            break
        time.sleep(interval_seconds)

    final_length = len(transcript)

    if not clipboard_tool:
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 1,
            "stdout": str(proc.stdout or "").strip(),
            "stderr": "No supported clipboard reader found. Install wl-paste, xclip, or xsel.",
            "command": command,
            "transcript": "",
            "method": "clipboard",
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": final_length,
            "changed": False,
            "error": "No supported clipboard reader found. Install wl-paste, xclip, or xsel.",
        }

    if not transcript or (require_change and not changed):
        error = "No new SpeechNote transcript detected."
        return {
            "ok": False,
            "provider": "speechnote",
            "exit_code": 1,
            "stdout": str(proc.stdout or "").strip(),
            "stderr": error,
            "command": command,
            "transcript": "",
            "method": "clipboard",
            "clipboard_tool": clipboard_tool,
            "initial_clipboard_length": initial_length,
            "final_clipboard_length": final_length,
            "changed": changed,
            "error": error,
        }

    return {
        "ok": True,
        "provider": "speechnote",
        "exit_code": 0,
        "stdout": str(proc.stdout or "").strip(),
        "stderr": str(proc.stderr or "").strip(),
        "command": command,
        "transcript": transcript,
        "method": "clipboard",
        "clipboard_tool": clipboard_tool,
        "initial_clipboard_length": initial_length,
        "final_clipboard_length": final_length,
        "changed": changed,
        "error": None,
    }
