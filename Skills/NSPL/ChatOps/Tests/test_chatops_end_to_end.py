import json
import os
import subprocess
import sys
import time
import unittest
import uuid
import shutil
from pathlib import Path

from Core.NSPL.NodeCTX import build_state_dir
from Core.NSPL.ProjectRoot import get_effective_root

def _rmtree_best_effort(path: Path, retries: int = 5, sleep_sec: float = 0.10) -> None:
    # I want teardown to be boring on every OS, even when Windows/AV holds a handle briefly.
    if not path.exists():
        return

    last_err: Exception | None = None
    for _ in range(retries):
        try:
            shutil.rmtree(path)
            return
        except Exception as exc:
            last_err = exc
            time.sleep(sleep_sec)

    # If it still fails, let the test fail loudly so we notice real lock/path bugs.
    if last_err is not None:
        raise last_err


def _run_skill(args, timeout=30):
    """Helper to run a SkillCLI command and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "Core.NSPL.SkillCLI"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(get_effective_root()),  # in case tests run from other dir
    )


class ChatOpsE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        # Each test uses a unique instance id to avoid interference
        self.instance = f"test_{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        # Clean up the State/<instance> directory after each test
        root = get_effective_root()
        state_dir = Path(root) / "State" / self.instance
        _rmtree_best_effort(state_dir)

    def test_happy_path_echo(self) -> None:
        # Enqueue a simple echo task
        cmd_send = [
            "skill",
            "ChatOps.send_task",
            "--instance",
            self.instance,
            "--skill",
            "Forge.Echo.echo",
            "--",
            "hello",
            "world",
        ]
        proc = _run_skill(cmd_send)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # Run the worker once to process the task
        cmd_worker = [
            "skill",
            "ChatOps.run_worker",
            "--instance",
            self.instance,
            "--once",
            "--poll-ms",
            "0",
        ]
        proc_w = _run_skill(cmd_worker)
        self.assertEqual(proc_w.returncode, 0, msg=proc_w.stderr)

        # Find the result file in the Done directory
        root = get_effective_root()
        done_dir = build_state_dir(
            root=root,
            instance_id=self.instance,
            node_tag="ignored",
            bucket="Workflow",
            domain="ChatOps",
            global_scope=True,
            subpath="Done",
        )
        files = list(Path(done_dir).glob("*.result.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "done")
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["skill"], "Forge.Echo.echo")
        self.assertEqual(data["args"], ["hello", "world"])

    def test_failing_task(self) -> None:
        # Enqueue a failing task using Forge.TestFail.fail
        cmd_send = [
            "skill",
            "ChatOps.send_task",
            "--instance",
            self.instance,
            "--skill",
            "Forge.TestFail.fail",
        ]
        proc = _run_skill(cmd_send)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # Run the worker once
        cmd_worker = [
            "skill",
            "ChatOps.run_worker",
            "--instance",
            self.instance,
            "--once",
            "--poll-ms",
            "0",
        ]
        proc_w = _run_skill(cmd_worker)
        self.assertEqual(proc_w.returncode, 0, msg=proc_w.stderr)

        # Verify that result is in Failed queue with status failed
        root = get_effective_root()
        failed_dir = build_state_dir(
            root=root,
            instance_id=self.instance,
            node_tag="ignored",
            bucket="Workflow",
            domain="ChatOps",
            global_scope=True,
            subpath="Failed",
        )
        files = list(Path(failed_dir).glob("*.result.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "failed")
        self.assertNotEqual(data["exit_code"], 0)
        self.assertEqual(data["skill"], "Forge.TestFail.fail")

    def test_queue_status_counts(self) -> None:
        # Enqueue two tasks; one will succeed, one will fail
        cmds = [
            [
                "skill",
                "ChatOps.send_task",
                "--instance",
                self.instance,
                "--skill",
                "Forge.Echo.echo",
                "--",
                "hi",
            ],
            [
                "skill",
                "ChatOps.send_task",
                "--instance",
                self.instance,
                "--skill",
                "Forge.TestFail.fail",
            ],
        ]
        for cmd in cmds:
            proc = _run_skill(cmd)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # Initially, queue_status should show 2 in Inbox
        proc_status = _run_skill(["skill", "ChatOps.queue_status", "--instance", self.instance, "--domain", "ChatOps"])
        self.assertEqual(proc_status.returncode, 0, msg=proc_status.stderr)
        # Parse counts from output (not JSON)
        lines = proc_status.stdout.strip().splitlines()
        counts = {}
        for line in lines:
            if ":" in line:
                name, count = line.split(":", 1)
                counts[name.strip()] = int(count.strip())
        self.assertEqual(counts.get("Inbox", 0), 2)
        self.assertEqual(counts.get("Claimed", 0), 0)
        self.assertEqual(counts.get("Done", 0), 0)
        self.assertEqual(counts.get("Failed", 0), 0)

        # Process two tasks with worker --once repeatedly
        for _ in range(2):
            proc_w = _run_skill([
                "skill",
                "ChatOps.run_worker",
                "--instance",
                self.instance,
                "--once",
                "--poll-ms",
                "0",
            ])
            self.assertEqual(proc_w.returncode, 0, msg=proc_w.stderr)

        # Now queue_status should show zero in Inbox and either Done or Failed counts
        proc_status2 = _run_skill(["skill", "ChatOps.queue_status", "--instance", self.instance, "--domain", "ChatOps"])
        self.assertEqual(proc_status2.returncode, 0, msg=proc_status2.stderr)
        lines2 = proc_status2.stdout.strip().splitlines()
        counts2 = {}
        for line in lines2:
            if ":" in line:
                name, count = line.split(":", 1)
                counts2[name.strip()] = int(count.strip())
        self.assertEqual(counts2.get("Inbox", 0), 0)
        # Exactly one done and one failed
        self.assertEqual(counts2.get("Done", 0) + counts2.get("Failed", 0), 2)
