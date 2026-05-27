from __future__ import annotations

import asyncio
import importlib.util
import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from Core.NSPL.Entry.web_context import SkillInvocationResult


REPO_ROOT = Path(__file__).resolve().parents[4]
STATUS_APP_PATH = REPO_ROOT / "Web" / "NSPL" / "Status" / "app.py"


def _load_status_module():
    spec = importlib.util.spec_from_file_location("_test_nspl_status_app", str(STATUS_APP_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Status app module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


@dataclass
class FakeStatusContext:
    repo_root: Path = REPO_ROOT
    app_dir: Path = REPO_ROOT / "Web" / "NSPL" / "Status"
    metadata: Dict[str, Any] | None = None
    calls: int = 0

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {"name": "NSPL.Status", "version": "0.1.0"}

    def run_skill(self, argv, timeout=30.0):
        raise AssertionError("Status app should use subprocess-backed skill invocation")

    def run_skill_subprocess(self, argv, timeout=30.0):
        self.calls += 1
        self.last_argv = list(argv)
        payload = {
            "display": "Friday, May 22, 2026 12:00 PM EDT",
            "timezone": "America/New_York",
            "utc_offset": "-04:00",
            "utc_iso": "2026-05-22T16:00:00+00:00",
            "time_12h": "12:00 PM",
        }
        return SkillInvocationResult(exit_code=0, stdout=json.dumps(payload), stderr="")


class StatusAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.status_module = _load_status_module()
        self.context = FakeStatusContext()
        self.app = self.status_module.create_app(self.context)

    def _endpoint(self, path: str):
        for route in self.app.routes:
            if getattr(route, "path", None) == path:
                return route.endpoint
        raise AssertionError(f"route not found: {path}")

    def test_health_returns_ok_json(self) -> None:
        result = asyncio.run(self._endpoint("/health")())

        self.assertEqual(result, {"ok": True, "app": "NSPL.Status"})

    def test_api_status_returns_app_time_and_skill_fields(self) -> None:
        result = asyncio.run(self._endpoint("/api/status")())

        self.assertEqual(result["app"], "NSPL.Status")
        self.assertEqual(result["version"], "0.1.0")
        self.assertEqual(result["repo_root"], str(REPO_ROOT))
        self.assertEqual(result["time"]["timezone"], "America/New_York")
        self.assertEqual(result["skill"]["exit_code"], 0)
        self.assertEqual(result["skill"]["stderr"], "")

    def test_status_app_uses_subprocess_skill_helper(self) -> None:
        result = asyncio.run(self._endpoint("/api/status")())

        self.assertEqual(self.context.calls, 1)
        self.assertEqual(
            self.context.last_argv,
            ["NSPL.Tools.Time.now", "--timezone", "America/New_York", "--json"],
        )
        self.assertEqual(result["skill"]["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
