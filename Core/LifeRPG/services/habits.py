from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.categories import canonical_category
from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Habit, to_record
from Core.LifeRPG.services import rewards
from Core.LifeRPG.time import today_key, utc_now_iso


def list_habits(store, *, include_archived: bool = False) -> list[dict]:
    ensure_defaults(store)
    habits = store.list_records("Data", ["Habits"])
    if not include_archived:
        habits = [habit for habit in habits if habit.get("status") not in {"archived", "deleted"}]
    return habits


def create(store, title: str, *, category: str = "Body", cadence: str = "daily") -> dict:
    ensure_defaults(store)
    clean_title = title.strip() or "Untitled Habit"
    habit = Habit(
        id=make_id("habit", utc_now_iso(), clean_title),
        title=clean_title,
        category=canonical_category(category, text=clean_title),
        cadence=str(cadence or "daily").strip() or "daily",
    )
    record = to_record(habit)
    store.write_json("Data", ["Habits"], f"{habit.id}.json", record)
    store.append_event("habit_created", {"habit_id": habit.id})
    return record


def get_habit(store, habit_id: str) -> dict:
    habit = store.read_json("Data", ["Habits"], f"{habit_id}.json")
    if not isinstance(habit, dict):
        raise ValueError(f"habit not found: {habit_id}")
    return habit


def edit(store, habit_id: str, *, title: str | None = None, category: str | None = None, cadence: str | None = None) -> dict:
    habit = get_habit(store, habit_id)
    if title is not None:
        habit["title"] = str(title).strip() or habit.get("title") or "Untitled Habit"
    if category is not None:
        habit["category"] = canonical_category(category, text=habit.get("title") or "")
    if cadence is not None:
        habit["cadence"] = str(cadence).strip() or "daily"
    habit["updated_at"] = utc_now_iso()
    store.write_json("Data", ["Habits"], f"{habit_id}.json", habit)
    store.append_event("habit_edited", {"habit_id": habit_id})
    return habit


def archive(store, habit_id: str, *, delete: bool = False) -> dict:
    habit = get_habit(store, habit_id)
    habit["status"] = "deleted" if delete else "archived"
    habit["archived_at"] = utc_now_iso()
    store.write_json("Data", ["Habits"], f"{habit_id}.json", habit)
    store.append_event("habit_deleted" if delete else "habit_archived", {"habit_id": habit_id})
    return habit


def check(store, habit_id: str) -> dict:
    ensure_defaults(store)
    habit = get_habit(store, habit_id)
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
