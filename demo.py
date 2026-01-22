from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RunResult:
    cmd: List[str]
    code: int
    stdout: str
    stderr: str


def _banner(title: str) -> None:
    line: str = "=" * 78
    print(f"\n{line}\n{title}\n{line}", flush=True)


def _print_cmd(cmd: Sequence[str]) -> None:
    print(f"\n$ {' '.join(str(x) for x in cmd)}", flush=True)


def _run(cmd: Sequence[str], *, cwd: Path, check: bool = True) -> RunResult:
    cmd_list: List[str] = [str(x) for x in cmd]
    _print_cmd(cmd_list)

    proc = subprocess.run(
        cmd_list,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )

    stdout: str = proc.stdout or ""
    stderr: str = proc.stderr or ""

    if stdout.strip():
        print(stdout.rstrip(), flush=True)

    if stderr.strip():
        print("[stderr]", flush=True)
        print(stderr.rstrip(), flush=True)

    result: RunResult = RunResult(
        cmd=cmd_list,
        code=int(proc.returncode),
        stdout=stdout,
        stderr=stderr,
    )

    if check and result.code != 0:
        raise SystemExit(f"[demo] Command failed (exit={result.code}): {' '.join(result.cmd)}")

    return result


def _wipe_state(repo_root: Path) -> None:
    state_dir: Path = repo_root / "State"
    if state_dir.exists():
        shutil.rmtree(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)


def _list_dir(dir_path: Path, *, label: str) -> None:
    if not dir_path.exists():
        print(f"[demo] {label}: (missing) {dir_path}", flush=True)
        return
    entries: List[Path] = sorted(dir_path.iterdir(), key=lambda p: p.name)
    print(f"[demo] {label}: {dir_path}", flush=True)
    if not entries:
        print("  (empty)", flush=True)
        return
    for p in entries:
        suffix: str = "/" if p.is_dir() else ""
        print(f"  - {p.name}{suffix}", flush=True)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_preview(obj: Any, *, max_chars: int = 1400) -> str:
    try:
        pretty: str = json.dumps(obj, indent=2, sort_keys=True)
        if len(pretty) > max_chars:
            return pretty[:max_chars].rstrip() + "\n... (truncated)"
        return pretty
    except Exception:
        return "<unprintable>"


def _find_latest_by_mtime(paths: List[Path]) -> Optional[Path]:
    if not paths:
        return None
    return sorted(paths, key=lambda p: p.stat().st_mtime)[-1]


def _glob_sorted(dir_path: Path, pattern: str) -> List[Path]:
    if not dir_path.exists():
        return []
    return sorted(list(dir_path.glob(pattern)), key=lambda p: p.name)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[demo] {message}")


def main() -> int:
    repo_root: Path = Path(__file__).resolve().parent
    python_exe: str = sys.executable
    instance_id: str = "main"

    _banner("NSPLite Demo — deterministic run: tests → enqueue → claim/exec → artifacts + logs")

    print(f"[demo] repo_root:  {repo_root}", flush=True)
    print(f"[demo] python:     {python_exe}", flush=True)
    print(f"[demo] instance:   {instance_id}", flush=True)

    _banner("0) Reset demo state (wipe State/ so this run is deterministic)")
    _wipe_state(repo_root)
    print("[demo] State/ wiped.", flush=True)

    _banner("1) Run test suite (proves core + skills are correct)")
    _run([python_exe, "run_tests.py"], cwd=repo_root, check=True)

    _banner("2) List skills via SkillCLI (proves discovery works without importing broken modules)")
    list_result: RunResult = _run([python_exe, "-m", "Core.SkillCLI", "list"], cwd=repo_root, check=True)

    expected: List[str] = [
        "ChatOps.send_task",
        "ChatOps.run_worker",
        "ChatOps.queue_status",
        "Forge.Echo.echo",
    ]
    missing: List[str] = []
    for name in expected:
        if name not in list_result.stdout:
            missing.append(name)
    _require(not missing, f"Missing expected skills from SkillCLI list: {missing}")

    # Paths we will prove/inspect
    workflow_dir: Path = repo_root / "State" / instance_id / "Global" / "Workflow" / "ChatOps"
    inbox_dir: Path = workflow_dir / "Inbox"
    claimed_dir: Path = workflow_dir / "Claimed"
    done_dir: Path = workflow_dir / "Done"
    failed_dir: Path = workflow_dir / "Failed"
    outbox_dir: Path = workflow_dir / "Outbox"
    outbox_path: Path = outbox_dir / "demo_result.json"

    logs_dir: Path = repo_root / "State" / instance_id / "Global" / "Logs" / "ChatOps" / "worker"

    _banner("3) Enqueue a task (producer writes JSON into Inbox/)")
    print(
        "\n".join(
            [
                "[demo] This writes a task file into the filesystem queue:",
                "  State/<instance>/Global/Workflow/ChatOps/Inbox/",
                "[demo] The worker will claim it (atomic rename), execute it, and write:",
                "  - Done/ (archival task + result)",
                "  - Outbox/ (reply_to writeback)",
                "  - Logs/ (events jsonl audit trail)",
            ]
        ),
        flush=True,
    )

    _list_dir(inbox_dir, label="Inbox BEFORE enqueue")

    payload_text: str = "Hello from demo.py"
    reply_to_rel: str = "Outbox/demo_result.json"

    _run(
        [
            python_exe,
            "-m",
            "Core.SkillCLI",
            "skill",
            "ChatOps.send_task",
            "--instance",
            instance_id,
            "--skill",
            "Forge.Echo.echo",
            "--reply-to",
            reply_to_rel,
            "--",
            payload_text,
        ],
        cwd=repo_root,
        check=True,
    )

    inbox_tasks: List[Path] = _glob_sorted(inbox_dir, "*.json")
    _require(len(inbox_tasks) == 1, f"Expected exactly 1 task in Inbox after enqueue, found {len(inbox_tasks)}")
    task_path: Path = inbox_tasks[0]

    task_obj: Dict[str, Any] = _read_json(task_path)
    task_id: str = str(task_obj.get("task_id", ""))

    _require(task_id != "", "Enqueued task JSON missing task_id")
    _require(task_obj.get("skill") == "Forge.Echo.echo", "Enqueued task skill mismatch (expected Forge.Echo.echo)")
    _require(task_obj.get("args") == [payload_text], "Enqueued task args mismatch")
    _require(
        isinstance(task_obj.get("reply_to"), dict) and task_obj["reply_to"].get("path") == reply_to_rel,
        "Enqueued task reply_to mismatch",
    )

    print(f"\n[demo] Enqueued task file:\n  {task_path}", flush=True)
    print("\n[demo] Task preview (this is what the worker will execute):", flush=True)
    print(_json_preview(task_obj), flush=True)

    _list_dir(inbox_dir, label="Inbox AFTER enqueue")

    _banner("4) Run worker ONCE (consumer claims → executes → transitions → writes artifacts)")
    _run(
        [
            python_exe,
            "-m",
            "Core.SkillCLI",
            "skill",
            "ChatOps.run_worker",
            "--instance",
            instance_id,
            "--once",
            "--idle-heartbeat-sec",
            "1.0",
            "--quiet-idle",
        ],
        cwd=repo_root,
        check=True,
    )

    _banner("5) Queue status (filesystem-backed counts)")
    _run(
        [
            python_exe,
            "-m",
            "Core.SkillCLI",
            "skill",
            "ChatOps.queue_status",
            "--instance",
            instance_id,
        ],
        cwd=repo_root,
        check=True,
    )

    _banner("6) Prove outcomes on disk (Inbox empty, Done contains audit trail, Outbox contains reply)")
    _list_dir(inbox_dir, label="Inbox AFTER worker (should be empty)")
    _list_dir(claimed_dir, label="Claimed AFTER worker (should be empty)")
    _list_dir(done_dir, label="Done AFTER worker (should contain task + result)")
    _list_dir(failed_dir, label="Failed AFTER worker (should be empty)")
    _list_dir(outbox_dir, label="Outbox AFTER worker (should contain demo_result.json)")
    _list_dir(logs_dir, label="Worker Logs dir (should contain *.events.jsonl)")

    # Outbox continuity checks
    _require(outbox_path.exists(), f"Expected reply_to outbox file missing: {outbox_path}")
    outbox_obj: Dict[str, Any] = _read_json(outbox_path)
    _require(str(outbox_obj.get("task_id", "")) == task_id, "Outbox task_id does not match enqueued task_id")
    _require(outbox_obj.get("status") == "done", "Outbox status expected 'done'")
    _require(outbox_obj.get("exit_code") == 0, "Outbox exit_code expected 0")
    _require(outbox_obj.get("stdout") == f"{payload_text}\n", "Outbox stdout mismatch (expected echo output)")

    # Done result continuity checks (best-effort: find latest .result.json and validate task_id)
    done_results: List[Path] = _glob_sorted(done_dir, "*.result.json")
    _require(len(done_results) >= 1, "Expected at least one *.result.json in Done/")
    done_result_path: Path = _find_latest_by_mtime(done_results) or done_results[-1]
    done_result_obj: Dict[str, Any] = _read_json(done_result_path)
    _require(str(done_result_obj.get("task_id", "")) == task_id, "Done result task_id does not match enqueued task_id")

    # Events log tail
    event_logs: List[Path] = _glob_sorted(logs_dir, "*.events.jsonl")
    _require(len(event_logs) >= 1, "Expected at least one worker *.events.jsonl log")
    events_path: Path = _find_latest_by_mtime(event_logs) or event_logs[-1]

    _banner("7) Outputs (the proof artifacts you can inspect)")
    print("[demo] Workflow (queues + outbox):", flush=True)
    print(f"  {workflow_dir}", flush=True)
    print("[demo] Worker logs (events jsonl):", flush=True)
    print(f"  {logs_dir}", flush=True)

    print("\n[demo] Outbox result (reply_to):", flush=True)
    print(f"  {outbox_path}", flush=True)
    print(_json_preview(outbox_obj), flush=True)

    print("\n[demo] Done/ result (archival audit trail):", flush=True)
    print(f"  {done_result_path}", flush=True)
    print(_json_preview(done_result_obj), flush=True)

    print("\n[demo] Worker events log tail (JSONL):", flush=True)
    print(f"  {events_path}", flush=True)
    try:
        lines: List[str] = events_path.read_text(encoding="utf-8").splitlines()
        tail: List[str] = lines[-40:] if len(lines) > 40 else lines
        print("\n".join(tail), flush=True)
    except Exception:
        print("<unable to read events log>", flush=True)

    _banner("Demo complete ✅  What this proved")
    print(
        "\n".join(
            [
                "• Tests passed (core + skills + e2e).",
                "• SkillCLI discovered skills from skill.json.",
                "• ChatOps.send_task wrote a task file into Inbox/ (filesystem queue).",
                "• ChatOps.run_worker atomically claimed the task, executed the target skill,",
                "  wrote durable results to Done/ and reply_to Outbox/, and emitted JSONL events.",
                "• Task ID continuity was validated across Inbox → Done → Outbox.",
            ]
        ),
        flush=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

