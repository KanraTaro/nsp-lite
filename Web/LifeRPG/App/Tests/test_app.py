from __future__ import annotations

import asyncio
import importlib.util
import json
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Core.NSPL.Entry.Discovery.web_loader import discover_web_apps
from Core.NSPL.Entry.web_context import SkillInvocationResult


REPO_ROOT = Path(__file__).resolve().parents[4]
APP_PATH = REPO_ROOT / "Web" / "LifeRPG" / "App" / "app.py"


def _load_app_module():
    spec = importlib.util.spec_from_file_location("_test_liferpg_app", str(APP_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load LifeRPG app")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


@dataclass
class FakeContext:
    repo_root: Path = REPO_ROOT
    app_dir: Path = REPO_ROOT / "Web" / "LifeRPG" / "App"
    metadata: dict[str, Any] = field(default_factory=lambda: {"name": "LifeRPG.App", "version": "0.1.0"})
    calls: list[list[str]] = field(default_factory=list)

    def run_skill(self, argv, timeout=30.0):
        self.calls.append(list(argv))
        name = argv[0]
        if name == "LifeRPG.Mission.Status":
            payload = {
                "mission": {"title": "Test Mission", "date": "2026-05-27", "focus": "test"},
                "habits": [{"id": "habit_1", "title": "Drink Water", "status": "open", "streak": 0, "tally": 0}],
                "events": [{"id": "event_1", "title": "Daily Reset", "starts_at": "2026-05-28T06:00:00Z"}],
                "quests": [{"id": "quest_1", "title": "Build Slice", "status": "open", "category": "Build", "minimum_win": "one step", "original_text": "build"}],
                "inbox": [{"id": "inbox_1", "title": "Fix Dad Page", "status": "sorted", "category": "Family", "minimum_win": "one step", "original_text": "fix dad page"}],
                "ledger": {"xp_total": 10, "leisure_tokens": 2, "entries": []},
                "active": {
                    "quest": {"id": "quest_1", "title": "Build Slice", "minimum_win": "one step"},
                    "session": {"id": "session_1", "status": "active"},
                    "expedition": {
                        "id": "exp_1",
                        "progress": 23,
                        "allies": [{"name": "Roh", "hp": 10, "max_hp": 10}],
                        "enemies": [{"name": "Chaos Echo", "hp": 8, "max_hp": 10}],
                        "log": ["started"],
                    },
                },
                "event_log": [],
                "roh_log": [],
            }
            return SkillInvocationResult(exit_code=0, stdout=json.dumps(payload), stderr="")
        return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True}), stderr="")


class LifeRPGWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_app_module()
        self.context = FakeContext()
        self.app = self.module.create_app(self.context)

    def _endpoint(self, path: str, method: str = "GET"):
        for route in self.app.routes:
            if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
                return route.endpoint
        raise AssertionError(f"route not found: {method} {path}")

    def _render(self, response) -> str:
        return response.template.render(response.context)

    def test_web_discovery_lists_liferpg_app(self) -> None:
        registry = discover_web_apps(REPO_ROOT / "Web")
        self.assertIn("LifeRPG.App", registry)

    def test_create_app_and_health(self) -> None:
        result = asyncio.run(self._endpoint("/health")())
        self.assertEqual(result, {"ok": True, "app": "LifeRPG.App"})

    def test_api_board_returns_status(self) -> None:
        result = asyncio.run(self._endpoint("/api/board")())
        self.assertEqual(result["mission"]["title"], "Test Mission")
        self.assertEqual(result["events"][0]["display_time"], "May 28, 6:00 AM")
        self.assertEqual(self.context.calls[-1], ["LifeRPG.Mission.Status", "--json"])

    def test_board_route_renders_stable_panel_ids(self) -> None:
        response = asyncio.run(self._endpoint("/")(_FakeRequest({})))
        html = self._render(response)

        for panel_id in (
            'id="mission-panel"',
            'id="habit-panel"',
            'id="inbox-panel"',
            'id="active-session-panel"',
            'id="expedition-panel"',
            'id="reward-panel"',
            'id="roh-actions-panel"',
        ):
            self.assertIn(panel_id, html)

    def test_habit_partial_uses_outer_panel_swap(self) -> None:
        response = asyncio.run(self._endpoint("/habit/check", "POST")(_FakeRequest({"habit_id": "habit_1"})))
        html = self._render(response)

        self.assertIn('id="habit-panel"', html)
        self.assertIn('hx-target="#habit-panel"', html)
        self.assertIn('hx-swap="outerHTML"', html)
        self.assertNotIn('hx-target="closest ' + 'section"', html)

    def test_expedition_partial_uses_outer_panel_swap(self) -> None:
        response = asyncio.run(self._endpoint("/expedition/tick", "POST")(_FakeRequest({})))
        html = self._render(response)

        self.assertIn('id="expedition-panel"', html)
        self.assertIn('hx-target="#expedition-panel"', html)
        self.assertIn('hx-swap="outerHTML"', html)

    def test_inbox_partial_uses_outer_panel_swap_targets(self) -> None:
        dump_response = asyncio.run(self._endpoint("/quick-dump", "POST")(_FakeRequest({"text": "fix dad page"})))
        dump_html = self._render(dump_response)
        sort_response = asyncio.run(self._endpoint("/sort", "POST")(_FakeRequest({})))
        sort_html = self._render(sort_response)
        board_html = self._render(asyncio.run(self._endpoint("/")(_FakeRequest({}))))

        self.assertIn('id="inbox-panel"', dump_html)
        self.assertIn('id="inbox-panel"', sort_html)
        self.assertIn('hx-target="#inbox-panel"', board_html)
        self.assertIn('hx-swap="outerHTML"', board_html)

    def test_quick_dump_sort_start_tick_and_habit_routes_call_skills(self) -> None:
        asyncio.run(self._endpoint("/quick-dump", "POST")(_FakeRequest({"text": "fix dad page"})))
        asyncio.run(self._endpoint("/sort", "POST")(_FakeRequest({})))
        asyncio.run(self._endpoint("/quest/start", "POST")(_FakeRequest({"inbox_id": "inbox_1", "quest_id": ""})))
        asyncio.run(self._endpoint("/expedition/tick", "POST")(_FakeRequest({})))
        asyncio.run(self._endpoint("/habit/check", "POST")(_FakeRequest({"habit_id": "habit_1"})))
        flat_calls = [" ".join(call) for call in self.context.calls]
        self.assertTrue(any("LifeRPG.Inbox.Add --text fix dad page --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Inbox.Sort --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Quest.Start --inbox-id inbox_1 --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Expedition.Tick --expedition-id exp_1 --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Habit.Check --habit-id habit_1 --json" in call for call in flat_calls))


class _FakeRequest:
    scope = {"type": "http", "method": "POST", "path": "/"}

    def __init__(self, data):
        self._data = data

    async def form(self):
        return self._data
