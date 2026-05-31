from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.services import events, habits, inbox, quests, rewards, sessions, settings


def current(store) -> dict:
    ensure_defaults(store)
    mission = store.read_json("Workflow", ["Missions"], "current_mission.json")
    return mission if isinstance(mission, dict) else {}


def board(store) -> dict:
    ensure_defaults(store)
    active = sessions.active_session_detail(store)
    payload = {
        "mission": current(store),
        "active": active,
        "quests": quests.list_quests(store),
        "inbox": inbox.list_items(store),
        "habits": habits.list_habits(store),
        "events": events.list_events(store),
        "settings": settings.get_settings(store),
        "ledger": rewards.get_ledger(store),
        "event_log": store.read_event_log()[-8:],
        "roh_log": store.read_event_log(roh=True)[-8:],
    }
    payload["roh_guidance"] = deterministic_guidance(payload)
    return payload


def deterministic_guidance(payload: dict) -> dict:
    inbox_items = [item for item in payload.get("inbox", []) if isinstance(item, dict) and item.get("status") in {"raw", "sorted"}]
    raw_items = [item for item in inbox_items if item.get("status") == "raw"]
    active = payload.get("active")
    quests = [quest for quest in payload.get("quests", []) if isinstance(quest, dict)]
    open_quests = [quest for quest in quests if quest.get("status") in {"open", "paused"}]
    habits_open = [habit for habit in payload.get("habits", []) if isinstance(habit, dict) and habit.get("status") != "checked"]

    if raw_items:
        return {
            "mode": "Template mode",
            "headline": "Sort your inbox next.",
            "detail": "Roh can turn raw dump items into project-aware quests with minimum wins.",
            "action": "Run Roh Sort",
        }
    if active and isinstance(active, dict) and active.get("quest"):
        quest = active["quest"]
        return {
            "mode": "Template mode",
            "headline": "Stay on the active quest.",
            "detail": f"Push {quest.get('title', 'this quest')} until the next check-in or complete the minimum win.",
            "action": "Add a progress note",
        }
    if open_quests:
        low_energy = sorted(open_quests, key=lambda quest: int(quest.get("energy_cost", 3) or 3))[0]
        return {
            "mode": "Template mode",
            "headline": "Start one low-energy quest.",
            "detail": f"Suggested next quest: {low_energy.get('title', 'Untitled Quest')}.",
            "action": "Start quest",
        }
    if habits_open:
        return {
            "mode": "Template mode",
            "headline": "Check one small habit.",
            "detail": "A quick habit check keeps momentum and grants a small reward.",
            "action": "Check habit",
        }
    return {
        "mode": "Template mode",
        "headline": "Quick Dump what is in your head.",
        "detail": "Capture the next loose thought, then sort it into a playable quest.",
        "action": "Quick Dump",
    }
