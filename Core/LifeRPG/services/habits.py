from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.services import rewards
from Core.LifeRPG.time import today_key, utc_now_iso


def list_habits(store) -> list[dict]:
    ensure_defaults(store)
    return store.list_records("Data", ["Habits"])


def check(store, habit_id: str) -> dict:
    ensure_defaults(store)
    habit = store.read_json("Data", ["Habits"], f"{habit_id}.json")
    if not isinstance(habit, dict):
        raise ValueError(f"habit not found: {habit_id}")
    already_today = str(habit.get("last_checked_at") or "").startswith(today_key())
    if not already_today:
        habit["streak"] = int(habit.get("streak", 0)) + 1
    habit["tally"] = int(habit.get("tally", 0)) + 1
    habit["status"] = "checked"
    habit["last_checked_at"] = utc_now_iso()
    store.write_json("Data", ["Habits"], f"{habit_id}.json", habit)
    reward = rewards.grant(store, source="habit", source_id=habit_id, xp=10, tokens=1, note=f"Checked {habit.get('title')}")
    store.append_event("habit_checked", {"habit_id": habit_id, "reward_id": reward["id"]})
    return {"habit": habit, "reward": reward}
