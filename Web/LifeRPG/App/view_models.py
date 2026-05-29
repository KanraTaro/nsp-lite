from __future__ import annotations

from typing import Any

from Web.LifeRPG.App.ui_choices import VISUAL_MODE


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _settings(payload: dict[str, Any]) -> dict[str, Any]:
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}
    result = {
        "display_name": "Operator",
        "timezone": "UTC",
        "auto_sort_enabled": False,
        "checkin_minutes": 90,
        "reward_intensity": "normal",
        "strictness_mode": "gentle",
        "visual_mode": "command_center",
    }
    result.update(settings)
    if result["visual_mode"] not in VISUAL_MODE:
        result["visual_mode"] = "command_center"
    return result


def board_view_model(payload: dict[str, Any], *, page: str = "board") -> dict[str, Any]:
    inbox = [item for item in _list(payload.get("inbox")) if item.get("status") not in {"quested", "archived", "deleted"}]
    quests = [quest for quest in _list(payload.get("quests")) if quest.get("status") != "archived"]
    habits = [habit for habit in _list(payload.get("habits")) if habit.get("status") != "archived"]
    events = [event for event in _list(payload.get("events")) if event.get("status") != "archived"]
    settings = _settings(payload)
    open_quests = [quest for quest in quests if quest.get("status") in {"open", "active", "paused"}]
    upcoming_events = [event for event in events if event.get("status") in {"scheduled", "active"}]

    return {
        "page": page,
        "settings": settings,
        "operator_name": settings.get("display_name") or "Operator",
        "body_class": f"visual-{settings.get('visual_mode', 'command_center')} page-{page}",
        "inbox_items": inbox,
        "inbox_preview": inbox[:4],
        "quest_items": quests,
        "quest_preview": open_quests[:4],
        "habit_items": habits,
        "habit_preview": habits[:5],
        "event_items": events,
        "event_preview": upcoming_events[:4],
        "has_more_inbox": len(inbox) > 4,
        "has_more_quests": len(open_quests) > 4,
        "has_more_habits": len(habits) > 5,
        "has_more_events": len(upcoming_events) > 4,
    }
