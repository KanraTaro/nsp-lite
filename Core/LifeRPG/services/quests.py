from __future__ import annotations

from Core.LifeRPG.categories import canonical_category
from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Quest, QuestSession, to_record
from Core.LifeRPG.services import expedition, inbox
from Core.LifeRPG.time import add_minutes, utc_now_iso


def list_quests(store, *, status: str | None = None) -> list[dict]:
    ensure_defaults(store)
    quests = store.list_records("Data", ["Quests"])
    if status:
        quests = [quest for quest in quests if quest.get("status") == status]
    return sorted(quests, key=lambda quest: str(quest.get("created_at", "")), reverse=True)


def _quest_from_inbox(store, inbox_id: str) -> dict:
    item = inbox.get_item(store, inbox_id)
    if item.get("quest_id"):
        existing = store.read_json("Data", ["Quests"], f"{item['quest_id']}.json")
        if isinstance(existing, dict):
            return existing
    quest = Quest(
        id=make_id("quest", item["id"], item.get("title") or item.get("original_text")),
        title=item.get("title") or item.get("original_text") or "Untitled Quest",
        original_text=item.get("original_text") or item.get("text") or "",
        category=canonical_category(item.get("category"), text=item.get("original_text") or ""),
        status="open",
        created_at=utc_now_iso(),
        minimum_win=item.get("minimum_win") or "",
        energy_cost=int(item.get("energy_cost", 1)),
        priority=int(item.get("priority", 3)),
        inbox_id=item["id"],
    )
    record = to_record(quest)
    store.write_json("Data", ["Quests"], f"{quest.id}.json", record)
    item["quest_id"] = quest.id
    item["status"] = "quested"
    inbox.save_item(store, item)
    store.append_event("quest_created", {"quest_id": quest.id, "inbox_id": item["id"]})
    return record


def create_simple(store, title: str, *, category: str = "Build") -> dict:
    quest = Quest(
        id=make_id("quest", utc_now_iso(), title),
        title=title.strip() or "Untitled Quest",
        original_text=title.strip(),
        category=canonical_category(category, text=title),
        status="open",
        created_at=utc_now_iso(),
        minimum_win=f"Move {title.strip() or 'the quest'} forward for 10 minutes.",
    )
    record = to_record(quest)
    store.write_json("Data", ["Quests"], f"{quest.id}.json", record)
    store.append_event("quest_created", {"quest_id": quest.id})
    return record


def get_quest(store, quest_id: str) -> dict:
    quest = store.read_json("Data", ["Quests"], f"{quest_id}.json")
    if not isinstance(quest, dict):
        raise ValueError(f"quest not found: {quest_id}")
    return quest


def start(store, *, quest_id: str | None = None, inbox_id: str | None = None) -> dict:
    ensure_defaults(store)
    quest = _quest_from_inbox(store, inbox_id) if inbox_id else get_quest(store, str(quest_id))
    if quest.get("active_session_id"):
        active = store.read_json("Workflow", ["Sessions", "active"], f"{quest['active_session_id']}.json")
        if isinstance(active, dict) and active.get("status") == "active":
            return {"quest": quest, "session": active, "expedition": expedition.get_active_for_session(store, active["id"])}
    started_at = utc_now_iso()
    session = QuestSession(
        id=make_id("session", quest["id"], started_at),
        quest_id=quest["id"],
        started_at=started_at,
        last_checkin_at=started_at,
        next_checkin_due_at=add_minutes(started_at, 90),
    )
    session_record = to_record(session)
    exp = expedition.start_for_session(store, quest, session_record)
    session_record["expedition_id"] = exp["id"]
    quest["status"] = "active"
    quest["active_session_id"] = session.id
    store.write_json("Workflow", ["Sessions", "active"], f"{session.id}.json", session_record)
    store.write_json("Data", ["Quests"], f"{quest['id']}.json", quest)
    store.append_event("quest_started", {"quest_id": quest["id"], "session_id": session.id, "expedition_id": exp["id"]})
    return {"quest": quest, "session": session_record, "expedition": exp}


def pause(store, quest_id: str, *, note: str = "", reason: str = "") -> dict:
    quest = get_quest(store, quest_id)
    session_id = quest.get("active_session_id")
    if not session_id:
        raise ValueError("quest has no active session")
    session = store.read_json("Workflow", ["Sessions", "active"], f"{session_id}.json")
    if not isinstance(session, dict):
        raise ValueError("active session not found")
    session["status"] = "paused"
    session["ended_at"] = utc_now_iso()
    session["note"] = note
    session["pause_reason"] = reason
    quest["status"] = "paused"
    quest["active_session_id"] = None
    store.write_json("Workflow", ["Sessions", "history"], f"{session_id}.json", session)
    store.node_ctx.delete_file(store.path("Workflow", ["Sessions", "active"], f"{session_id}.json"), missing_ok=True)
    store.write_json("Data", ["Quests"], f"{quest_id}.json", quest)
    store.append_event("quest_paused", {"quest_id": quest_id, "session_id": session_id, "reason": reason, "note": note})
    return {"quest": quest, "session": session}


def complete(store, quest_id: str, *, note: str = "") -> dict:
    quest = get_quest(store, quest_id)
    session_id = quest.get("active_session_id")
    session = None
    exp = None
    if session_id:
        session = store.read_json("Workflow", ["Sessions", "active"], f"{session_id}.json")
        if isinstance(session, dict):
            session["status"] = "completed"
            session["ended_at"] = utc_now_iso()
            session["note"] = note
            exp = expedition.resolve_for_session(store, session_id, note=note)
            store.write_json("Workflow", ["Sessions", "history"], f"{session_id}.json", session)
            store.node_ctx.delete_file(store.path("Workflow", ["Sessions", "active"], f"{session_id}.json"), missing_ok=True)
    quest["status"] = "completed"
    quest["completed_at"] = utc_now_iso()
    quest["active_session_id"] = None
    store.write_json("Data", ["Quests"], f"{quest_id}.json", quest)
    reward = expedition.grant_completion_reward(store, quest, exp)
    store.append_event("quest_completed", {"quest_id": quest_id, "session_id": session_id, "reward_id": reward["id"], "note": note})
    return {"quest": quest, "session": session, "expedition": exp, "reward": reward}
