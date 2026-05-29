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
    return {
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
