from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults


def active_sessions(store) -> list[dict]:
    ensure_defaults(store)
    return store.list_records("Workflow", ["Sessions", "active"])


def active_session_detail(store) -> dict | None:
    sessions = active_sessions(store)
    if not sessions:
        return None
    session = sessions[-1]
    quest = store.read_json("Data", ["Quests"], f"{session['quest_id']}.json")
    expedition = None
    if session.get("expedition_id"):
        expedition = store.read_json("Workflow", ["Expeditions", "active"], f"{session['expedition_id']}.json")
    return {"session": session, "quest": quest if isinstance(quest, dict) else None, "expedition": expedition if isinstance(expedition, dict) else None}


def history_for_quest(store, quest_id: str) -> list[dict]:
    history = [session for session in store.list_records("Workflow", ["Sessions", "history"]) if session.get("quest_id") == quest_id]
    return sorted(history, key=lambda session: str(session.get("started_at") or session.get("id") or ""), reverse=True)
