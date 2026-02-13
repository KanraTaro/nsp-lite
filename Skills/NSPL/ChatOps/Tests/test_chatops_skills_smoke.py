import subprocess
import sys
import uuid
import unittest
import shutil
import time
from pathlib import Path

from Core.NSPL.ProjectRoot import get_effective_root



def _run_skillcli(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "Core.NSPL.SkillCLI"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(get_effective_root()),  # in case tests run from other dir
    )


def _rm_tree(path: Path, retries: int = 5, sleep_sec: float = 0.10) -> None:
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

    if last_err is not None:
        raise last_err


class ChatOpsSkillsSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance_id = f"smoke_{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        root = Path(get_effective_root())
        state_dir = root / "State" / self.instance_id
        _rm_tree(state_dir)

    def test_queue_status_runs_empty(self) -> None:
        proc = _run_skillcli(
            ["skill", "ChatOps.queue_status", "--instance", self.instance_id, "--domain", "ChatOps"]
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        # Should print the four queue counts in human mode
        self.assertIn("Inbox:", proc.stdout)
        self.assertIn("Claimed:", proc.stdout)
        self.assertIn("Done:", proc.stdout)
        self.assertIn("Failed:", proc.stdout)

    def test_send_task_increments_inbox(self) -> None:
        # Enqueue one task
        proc_send = _run_skillcli(
            [
                "skill",
                "ChatOps.send_task",
                "--instance",
                self.instance_id,
                "--skill",
                "Tools.Echo.echo",
                "--",
                "smoke",
                "test",
            ]
        )
        self.assertEqual(proc_send.returncode, 0, msg=proc_send.stderr)
        self.assertIn("task_id=", proc_send.stdout)

        # Verify queue status shows 1 in Inbox
        proc_status = _run_skillcli(
            ["skill", "ChatOps.queue_status", "--instance", self.instance_id, "--domain", "ChatOps"]
        )
        self.assertEqual(proc_status.returncode, 0, msg=proc_status.stderr)

        counts: dict[str, int] = {}
        for line in proc_status.stdout.strip().splitlines():
            if ":" not in line:
                continue
            name, count = line.split(":", 1)
            counts[name.strip()] = int(count.strip())

        self.assertEqual(counts.get("Inbox", 0), 1)

