from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Expedition, Threat, to_record
from Core.LifeRPG.services import rewards
from Core.LifeRPG.time import parse_utc, utc_now, utc_now_iso


def _enemy_for(category: str, quest_id: str) -> dict:
    names = {
        "Build": "Scope Wraith",
        "Home": "Clutter Drone",
        "Family": "Concern Shade",
        "Admin": "Paperwork Hydra",
        "Body": "Friction Impulse",
    }
    threat = Threat(id=make_id("enemy", quest_id, category), name=names.get(category, "Chaos Echo"), hp=240, max_hp=240, power=8)
    return to_record(threat)


def start_for_session(store, quest: dict, session: dict) -> dict:
    ensure_defaults(store)
    agents = store.list_records("Data", ["Agents"])[:3]
    expedition = Expedition(
        id=make_id("expedition", session["id"], quest["id"]),
        quest_id=quest["id"],
        session_id=session["id"],
        status="active",
        created_at=utc_now_iso(),
        allies=agents,
        enemies=[_enemy_for(str(quest.get("category") or "Survival"), quest["id"])],
        log=[f"Roh opened an expedition for {quest.get('title')}."],
    )
    record = to_record(expedition)
    store.write_json("Workflow", ["Expeditions", "active"], f"{expedition.id}.json", record)
    store.append_event("expedition_started", {"expedition_id": expedition.id, "quest_id": quest["id"], "session_id": session["id"]})
    return record


def get_active_for_session(store, session_id: str) -> dict | None:
    for expedition in store.list_records("Workflow", ["Expeditions", "active"]):
        if expedition.get("session_id") == session_id and expedition.get("status") == "active":
            return expedition
    return None


def active_expeditions(store) -> list[dict]:
    ensure_defaults(store)
    return store.list_records("Workflow", ["Expeditions", "active"])


def tick(store, expedition_id: str | None = None) -> dict:
    ensure_defaults(store)
    expedition = None
    if expedition_id:
        expedition = store.read_json("Workflow", ["Expeditions", "active"], f"{expedition_id}.json")
    else:
        active = active_expeditions(store)
        expedition = active[-1] if active else None
    if not isinstance(expedition, dict):
        raise ValueError("no active expedition")
    session = store.read_json("Workflow", ["Sessions", "active"], f"{expedition['session_id']}.json")
    if isinstance(session, dict):
        due = session.get("next_checkin_due_at")
        if due and parse_utc(due) < utc_now():
            session["status"] = "awaiting_checkin"
            expedition["status"] = "awaiting_checkin"
            expedition.setdefault("log", []).append("Roh paused the expedition for a check-in.")
            store.write_json("Workflow", ["Sessions", "active"], f"{session['id']}.json", session)
            store.write_json("Workflow", ["Expeditions", "active"], f"{expedition['id']}.json", expedition)
            return expedition
    ticks = int(expedition.get("ticks", 0)) + 1
    expedition["ticks"] = ticks
    expedition["progress"] = min(100, int(expedition.get("progress", 0)) + 9 + (ticks % 4))
    enemies = list(expedition.get("enemies") or [])
    allies = list(expedition.get("allies") or [])
    if enemies:
        target = enemies[ticks % len(enemies)]
        damage = 12 + sum(int(agent.get("power", 0)) for agent in allies) // max(1, len(allies))
        target["hp"] = max(0, int(target.get("hp", 0)) - damage)
        expedition["enemies"] = enemies
        expedition.setdefault("log", []).append(f"Tick {ticks}: agents dealt {damage} to {target.get('name')}.")
    if allies and ticks % 2 == 0:
        target = allies[ticks % len(allies)]
        damage = 3 + (sum(int(enemy.get("power", 0)) for enemy in enemies) // max(1, len(enemies)))
        target["hp"] = max(1, int(target.get("hp", 0)) - damage)
        expedition["allies"] = allies
        expedition.setdefault("log", []).append(f"Tick {ticks}: {target.get('name')} held formation after {damage} pressure.")
    expedition["log"] = expedition.get("log", [])[-8:]
    store.write_json("Workflow", ["Expeditions", "active"], f"{expedition['id']}.json", expedition)
    store.append_event("expedition_tick", {"expedition_id": expedition["id"], "progress": expedition["progress"]})
    return expedition


def resolve_for_session(store, session_id: str, *, note: str = "") -> dict | None:
    expedition = get_active_for_session(store, session_id)
    if not expedition:
        return None
    expedition["status"] = "completed"
    expedition["progress"] = 100
    expedition["resolved_at"] = utc_now_iso()
    expedition.setdefault("log", []).append(note or "Quest complete. Roh extracted the party and logged rewards.")
    store.write_json("Workflow", ["Expeditions", "history"], f"{expedition['id']}.json", expedition)
    store.node_ctx.delete_file(store.path("Workflow", ["Expeditions", "active"], f"{expedition['id']}.json"), missing_ok=True)
    store.append_event("expedition_resolved", {"expedition_id": expedition["id"], "session_id": session_id})
    return expedition


def grant_completion_reward(store, quest: dict, expedition: dict | None) -> dict:
    xp = 40 + int(quest.get("priority", 3)) * 15 + int(quest.get("energy_cost", 1)) * 5
    tokens = 5 + int(quest.get("priority", 3)) * 2
    if expedition:
        xp += int(expedition.get("progress", 0)) // 4
    return rewards.grant(store, source="quest", source_id=quest["id"], xp=xp, tokens=tokens, note=f"Completed {quest.get('title')}")
