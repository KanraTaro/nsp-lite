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
    settings: dict[str, Any] = field(
        default_factory=lambda: {
            "display_name": "Operator",
            "timezone": "UTC",
            "auto_sort_enabled": True,
            "checkin_minutes": 90,
            "reward_intensity": "normal",
            "strictness_mode": "gentle",
            "visual_mode": "command_center",
        }
    )

    def run_skill(self, argv, timeout=30.0):
        self.calls.append(list(argv))
        name = argv[0]
        if name == "LifeRPG.Mission.Status":
            payload = {
                "mission": {"title": "Test Mission", "date": "2026-05-27", "focus": "test"},
                "habits": [{"id": "habit_1", "title": "Drink Water", "status": "open", "streak": 0, "tally": 0, "category": "Body", "cadence": "daily"}],
                "events": [{"id": "event_1", "title": "Daily Reset", "starts_at": "2026-05-28T06:00:00Z", "status": "scheduled", "reminder_minutes": [60]}],
                "quests": [{"id": "quest_1", "title": "Build Slice", "status": "open", "project": "Example Project", "category": "Build", "minimum_win": "one step", "original_text": "build", "priority": 2, "energy_cost": 1, "steps": [{"id": "step_1", "title": "Open editor", "status": "open"}], "notes": [{"id": "note_1", "created_at": "2026-05-28T06:10:00Z", "text": "progress"}]}],
                "inbox": [{"id": "inbox_1", "title": "Fix Page", "status": "sorted", "project": "Example Project", "category": "Build", "minimum_win": "one step", "original_text": "fix example page", "priority": 1, "energy_cost": 2, "previous_state": {"status": "raw"}}],
                "ledger": {"xp_total": 10, "leisure_tokens": 2, "entries": [{"id": "reward_1", "source": "quest", "source_id": "quest_1", "xp": 25, "tokens": 2, "note": "Quest completed"}]},
                "settings": dict(self.settings),
                "active": {
                    "quest": {"id": "quest_1", "title": "Build Slice", "project": "Example Project", "category": "Build", "minimum_win": "one step"},
                    "session": {"id": "session_1", "status": "active", "started_at": "2026-05-28T06:00:00Z", "latest_note": "working"},
                    "expedition": {
                        "id": "exp_1",
                        "progress": 23,
                        "allies": [{"name": "Roh", "hp": 10, "max_hp": 10}],
                        "enemies": [{"name": "Chaos Echo", "hp": 8, "max_hp": 10}],
                        "log": ["started"],
                    },
                },
                "event_log": [],
                "roh_log": [{"kind": "roh_sort_completed", "count": 2}],
                "roh_guidance": {"mode": "Template mode", "headline": "Stay on the active quest.", "detail": "Push the minimum win.", "action": "Add a progress note"},
            }
            return SkillInvocationResult(exit_code=0, stdout=json.dumps(payload), stderr="")
        if name == "LifeRPG.Quest.Detail":
            payload = {
                "quest": {
                    "id": "quest_1",
                    "title": "Build Slice",
                    "original_text": "build",
                    "project": "Example Project",
                    "category": "Build",
                    "status": "active",
                    "priority": 2,
                    "energy_cost": 1,
                    "minimum_win": "one step",
                    "active_session_id": "session_1",
                    "steps": [{"id": "step_1", "title": "Open editor", "status": "open"}],
                    "notes": [{"id": "note_1", "created_at": "2026-05-28T06:10:00Z", "text": "progress"}],
                },
                "active": {"session": {"id": "session_1", "started_at": "2026-05-28T06:00:00Z", "next_checkin_due_at": "2026-05-28T07:30:00Z"}, "expedition": {"progress": 23}},
                "sessions": [{"id": "session_old", "status": "paused", "started_at": "2026-05-27T06:00:00Z", "ended_at": "2026-05-27T06:30:00Z", "note": "paused"}],
                "rewards": [{"id": "reward_1", "xp": 25, "tokens": 2, "note": "Quest completed"}],
            }
            return SkillInvocationResult(exit_code=0, stdout=json.dumps(payload), stderr="")
        if name == "LifeRPG.Settings.Update":
            for index, token in enumerate(argv):
                if token == "--display-name" and index + 1 < len(argv):
                    self.settings["display_name"] = argv[index + 1]
                if token == "--auto-sort-enabled" and index + 1 < len(argv):
                    self.settings["auto_sort_enabled"] = argv[index + 1] == "true"
                if token == "--checkin-minutes" and index + 1 < len(argv):
                    self.settings["checkin_minutes"] = int(argv[index + 1])
                if token == "--visual-mode" and index + 1 < len(argv):
                    self.settings["visual_mode"] = argv[index + 1]
            return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True, "settings": self.settings}), stderr="")
        if name == "LifeRPG.Habit.Check":
            return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True, "xp": 10, "tokens": 1}), stderr="")
        if name == "LifeRPG.Quest.Complete":
            return SkillInvocationResult(exit_code=0, stdout=json.dumps({"ok": True, "xp": 25, "tokens": 2}), stderr="")
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
            'id="quest-panel"',
            'id="active-session-panel"',
            'id="expedition-panel"',
            'id="reward-panel"',
            'id="roh-actions-panel"',
        ):
            self.assertIn(panel_id, html)

    def test_board_is_compact_preview_with_management_links(self) -> None:
        response = asyncio.run(self._endpoint("/")(_FakeRequest({})))
        html = self._render(response)

        self.assertIn("Manage Inbox", html)
        self.assertIn("Manage Quests", html)
        self.assertIn("Manage Habits", html)
        self.assertIn("Manage Events", html)
        self.assertNotIn('hx-post="/inbox/edit"', html)
        self.assertNotIn('hx-post="/quest/edit"', html)
        self.assertNotIn('hx-post="/habit/edit"', html)
        self.assertNotIn('hx-post="/event/edit"', html)

    def test_board_shows_project_chips_guidance_and_reward_feedback(self) -> None:
        html = self._render(asyncio.run(self._endpoint("/")(_FakeRequest({}))))

        self.assertIn("Example Project", html)
        self.assertIn("Stay on the active quest.", html)
        self.assertIn("+25 XP", html)
        self.assertIn("Add Note", html)
        self.assertIn('id="topbar-rewards"', html)
        self.assertIn("reward-feedback", html)

    def test_management_pages_use_selects_for_choice_fields(self) -> None:
        inbox_html = self._render(asyncio.run(self._endpoint("/inbox")(_FakeRequest({}))))
        quests_html = self._render(asyncio.run(self._endpoint("/quests")(_FakeRequest({}))))
        today_html = self._render(asyncio.run(self._endpoint("/today")(_FakeRequest({}))))
        settings_html = self._render(asyncio.run(self._endpoint("/settings")(_FakeRequest({}))))

        self.assertIn('<select name="category"', inbox_html)
        self.assertIn('<select name="category"', quests_html)
        self.assertIn('<select name="project"', inbox_html)
        self.assertIn('<select name="project"', quests_html)
        self.assertIn('<select name="status"', quests_html)
        self.assertIn('<select name="cadence"', today_html)
        self.assertIn('<select name="status"', today_html)
        self.assertIn('<select name="reward_intensity"', settings_html)
        self.assertIn('<select name="strictness_mode"', settings_html)
        self.assertIn('<select name="visual_mode"', settings_html)
        self.assertIn("balanced", settings_html)
        self.assertIn("mobile", settings_html)

    def test_settings_save_updates_display_name_and_visual_class(self) -> None:
        asyncio.run(
            self._endpoint("/settings/save", "POST")(
                _FakeRequest(
                    {
                        "display_name": "Operator Two",
                        "timezone": "UTC",
                        "auto_sort_enabled": "true",
                        "checkin_minutes": "45",
                        "visual_mode": "compact",
                    }
                )
            )
        )
        html = self._render(asyncio.run(self._endpoint("/")(_FakeRequest({}))))

        self.assertIn("Operator Two command profile", html)
        self.assertIn('class="visual-compact page-board"', html)

    def test_quick_dump_auto_sort_uses_sort_path(self) -> None:
        asyncio.run(self._endpoint("/quick-dump", "POST")(_FakeRequest({"text": "fix sample page"})))
        flat_calls = [" ".join(call) for call in self.context.calls]

        self.assertTrue(any("LifeRPG.Inbox.Add --text fix sample page --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Inbox.Sort --json" in call for call in flat_calls))

    def test_start_complete_and_habit_check_return_cross_panel_updates(self) -> None:
        start = self._render(asyncio.run(self._endpoint("/quest/start", "POST")(_FakeRequest({"quest_id": "quest_1"}))))
        complete = self._render(asyncio.run(self._endpoint("/quest/complete", "POST")(_FakeRequest({"quest_id": "quest_1"}))))
        habit = self._render(asyncio.run(self._endpoint("/habit/check", "POST")(_FakeRequest({"habit_id": "habit_1"}))))

        self.assertIn('id="active-session-panel"', start)
        self.assertIn('id="expedition-panel" class="panel expedition" hx-swap-oob="outerHTML"', start)
        self.assertIn('id="quest-panel" class="panel" hx-swap-oob="outerHTML"', start)
        self.assertIn("Quest completed. Rewards resolved.", complete)
        self.assertIn('id="reward-panel"', complete)
        self.assertIn('hx-swap-oob="outerHTML"', complete)
        self.assertIn('id="topbar-rewards"', complete)
        self.assertIn('id="topbar-rewards"', habit)
        self.assertIn("reward-feedback", complete)

    def test_raw_roh_event_keys_do_not_render(self) -> None:
        board_html = self._render(asyncio.run(self._endpoint("/")(_FakeRequest({}))))
        roh_html = self._render(asyncio.run(self._endpoint("/roh")(_FakeRequest({}))))

        self.assertNotIn("roh_sort_completed", board_html)
        self.assertNotIn("roh_sort_completed", roh_html)
        self.assertIn("Template mode: deterministic guidance, not live RohTalk yet.", board_html)

    def test_quest_detail_page_shows_notes_sessions_and_actions(self) -> None:
        response = asyncio.run(self._endpoint("/quests/{quest_id}")(_FakeRequest({}), "quest_1"))
        html = self._render(response)

        self.assertIn('id="quest-detail-panel"', html)
        self.assertIn("Original: build", html)
        self.assertIn("Example Project", html)
        self.assertIn("progress", html)
        self.assertIn("Session History", html)
        self.assertIn("paused", html)
        self.assertIn("Quest completed", html)
        self.assertIn('action="/quest/add-note"', html)

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
        dump_response = asyncio.run(self._endpoint("/quick-dump", "POST")(_FakeRequest({"text": "fix sample page"})))
        dump_html = self._render(dump_response)
        sort_response = asyncio.run(self._endpoint("/sort", "POST")(_FakeRequest({})))
        sort_html = self._render(sort_response)
        board_html = self._render(asyncio.run(self._endpoint("/")(_FakeRequest({}))))

        self.assertIn('id="inbox-panel"', dump_html)
        self.assertIn('id="inbox-panel"', sort_html)
        self.assertIn('hx-target="#inbox-panel"', board_html)
        self.assertIn('hx-swap="outerHTML"', board_html)

    def test_quick_dump_sort_start_tick_and_habit_routes_call_skills(self) -> None:
        asyncio.run(self._endpoint("/quick-dump", "POST")(_FakeRequest({"text": "fix sample page"})))
        asyncio.run(self._endpoint("/sort", "POST")(_FakeRequest({})))
        asyncio.run(self._endpoint("/quest/start", "POST")(_FakeRequest({"inbox_id": "inbox_1", "quest_id": ""})))
        asyncio.run(self._endpoint("/expedition/tick", "POST")(_FakeRequest({})))
        asyncio.run(self._endpoint("/habit/check", "POST")(_FakeRequest({"habit_id": "habit_1"})))
        flat_calls = [" ".join(call) for call in self.context.calls]
        self.assertTrue(any("LifeRPG.Inbox.Add --text fix sample page --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Inbox.Sort --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Quest.Start --inbox-id inbox_1 --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Expedition.Tick --expedition-id exp_1 --json" in call for call in flat_calls))
        self.assertTrue(any("LifeRPG.Habit.Check --habit-id habit_1 --json" in call for call in flat_calls))

    def test_inbox_management_routes_use_stable_panel_and_flat_skills(self) -> None:
        for path, data, expected in (
            ("/inbox/edit", {"inbox_id": "inbox_1", "title": "Fix Dad Page", "priority": "1"}, "LifeRPG.Inbox.Edit --inbox-id inbox_1"),
            ("/inbox/revert", {"inbox_id": "inbox_1"}, "LifeRPG.Inbox.Revert --inbox-id inbox_1"),
            ("/inbox/archive", {"inbox_id": "inbox_1"}, "LifeRPG.Inbox.Archive --inbox-id inbox_1"),
        ):
            response = asyncio.run(self._endpoint(path, "POST")(_FakeRequest(data)))
            html = self._render(response)
            self.assertIn('id="inbox-panel"', html)
            self.assertIn('hx-target="#inbox-panel"', html)
            self.assertIn('hx-swap="outerHTML"', html)
            self.assertIn("notice success", html)
            self.assertTrue(any(expected in " ".join(call) for call in self.context.calls))

    def test_quest_management_routes_use_stable_panel(self) -> None:
        routes = (
            ("/quest/create", {"title": "New Quest"}, "LifeRPG.Quest.Create --title New Quest"),
            ("/quest/edit", {"quest_id": "quest_1", "title": "Build Slice", "project": "Example Project"}, "LifeRPG.Quest.Edit --quest-id quest_1"),
            ("/quest/add-step", {"quest_id": "quest_1", "title": "Write test"}, "LifeRPG.Quest.AddStep --quest-id quest_1"),
            ("/quest/check-step", {"quest_id": "quest_1", "step_id": "step_1"}, "LifeRPG.Quest.CheckStep --quest-id quest_1"),
            ("/quest/add-note", {"quest_id": "quest_1", "note": "note"}, "LifeRPG.Quest.AddNote --quest-id quest_1"),
            ("/quest/archive", {"quest_id": "quest_1"}, "LifeRPG.Quest.Archive --quest-id quest_1"),
        )
        for path, data, expected in routes:
            response = asyncio.run(self._endpoint(path, "POST")(_FakeRequest(data)))
            html = self._render(response)
            self.assertIn('id="quest-panel"', html)
            self.assertIn('hx-target="#quest-panel"', html)
            self.assertIn('hx-swap="outerHTML"', html)
            self.assertIn("notice success", html)
            self.assertTrue(any(expected in " ".join(call) for call in self.context.calls))

    def test_quest_detail_post_actions_redirect_to_detail_url(self) -> None:
        routes = (
            ("/quest/add-note", {"quest_id": "quest_1", "note": "detail note", "return": "detail"}, "LifeRPG.Quest.AddNote --quest-id quest_1"),
            ("/quest/start", {"quest_id": "quest_1", "return": "detail"}, "LifeRPG.Quest.Start --quest-id quest_1"),
            ("/quest/pause", {"quest_id": "quest_1", "note": "paused", "return": "detail"}, "LifeRPG.Quest.Pause --quest-id quest_1"),
            ("/quest/complete", {"quest_id": "quest_1", "note": "done", "return": "detail"}, "LifeRPG.Quest.Complete --quest-id quest_1"),
        )
        for path, data, expected in routes:
            response = asyncio.run(self._endpoint(path, "POST")(_FakeRequest(data)))
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/quests/quest_1")
            self.assertTrue(any(expected in " ".join(call) for call in self.context.calls))

    def test_management_pages_collapse_secondary_actions(self) -> None:
        inbox_html = self._render(asyncio.run(self._endpoint("/inbox")(_FakeRequest({}))))
        quests_html = self._render(asyncio.run(self._endpoint("/quests")(_FakeRequest({}))))
        today_html = self._render(asyncio.run(self._endpoint("/today")(_FakeRequest({}))))

        for html in (inbox_html, quests_html, today_html):
            self.assertIn('class="management-more"', html)
            self.assertIn("<summary>More</summary>", html)
        self.assertLess(inbox_html.find("More"), inbox_html.find("Archive"))
        self.assertLess(quests_html.find("More"), quests_html.find("Archive"))
        self.assertLess(today_html.find("More"), today_html.find("Archive"))

    def test_active_progress_note_returns_session_panel(self) -> None:
        response = asyncio.run(self._endpoint("/quest/progress-note", "POST")(_FakeRequest({"quest_id": "quest_1", "note": "progress note"})))
        html = self._render(response)

        self.assertIn('id="active-session-panel"', html)
        self.assertIn("Progress note added.", html)
        self.assertTrue(any("LifeRPG.Quest.AddNote --quest-id quest_1 --note progress note" in " ".join(call) for call in self.context.calls))

    def test_habit_event_and_settings_management_routes(self) -> None:
        routes = (
            ("/habit/create", {"title": "Stretch"}, 'id="habit-panel"', "LifeRPG.Habit.Create --title Stretch"),
            ("/habit/edit", {"habit_id": "habit_1", "title": "Drink Water"}, 'id="habit-panel"', "LifeRPG.Habit.Edit --habit-id habit_1"),
            ("/habit/archive", {"habit_id": "habit_1"}, 'id="habit-panel"', "LifeRPG.Habit.Archive --habit-id habit_1"),
            ("/event/create", {"title": "Reset", "starts_at": "2026-05-28T06:00"}, 'id="event-panel"', "LifeRPG.Event.Create --title Reset"),
            ("/event/edit", {"event_id": "event_1", "title": "Daily Reset"}, 'id="event-panel"', "LifeRPG.Event.Edit --event-id event_1"),
            ("/event/archive", {"event_id": "event_1"}, 'id="event-panel"', "LifeRPG.Event.Archive --event-id event_1"),
            ("/settings/save", {"display_name": "Operator Two", "timezone": "UTC", "auto_sort_enabled": "true", "checkin_minutes": "45"}, 'id="settings-panel"', "LifeRPG.Settings.Update --display-name Operator Two"),
        )
        for path, data, panel_id, expected in routes:
            response = asyncio.run(self._endpoint(path, "POST")(_FakeRequest(data)))
            html = self._render(response)
            self.assertIn(panel_id, html)
            self.assertIn('hx-swap="outerHTML"', html)
            self.assertIn("notice success", html)
            self.assertTrue(any(expected in " ".join(call) for call in self.context.calls))

    def test_settings_page_renders(self) -> None:
        response = asyncio.run(self._endpoint("/settings")(_FakeRequest({})))
        html = self._render(response)
        self.assertIn('id="settings-panel"', html)
        self.assertIn('hx-target="#settings-panel"', html)


class _FakeRequest:
    scope = {"type": "http", "method": "POST", "path": "/"}

    def __init__(self, data):
        self._data = data

    async def form(self):
        return self._data
