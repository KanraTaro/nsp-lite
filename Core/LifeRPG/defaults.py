from __future__ import annotations

from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Agent, Event, Habit, Mission, TokenLedger, to_record
from Core.LifeRPG.time import today_key, utc_now_iso


DEFAULT_SETTINGS = {
    "display_name": "Operator",
    "timezone": "UTC",
    "default_scope": "Global",
    "auto_sort_enabled": False,
    "checkin_minutes": 90,
    "reward_intensity": "normal",
    "strictness_mode": "gentle",
    "visual_mode": "command_center",
}


def ensure_defaults(store) -> None:
    profile = store.read_json("Config", "", "profile.json")
    if profile is None:
        store.write_json("Config", "", "profile.json", {k: DEFAULT_SETTINGS[k] for k in ["display_name", "timezone", "default_scope"]})
    settings = store.read_json("Config", "", "settings.json")
    if settings is None:
        store.write_json("Config", "", "settings.json", DEFAULT_SETTINGS)
    elif isinstance(settings, dict):
        merged = {**DEFAULT_SETTINGS, **settings}
        store.write_json("Config", "", "settings.json", merged)
    if store.read_json("Data", "", "categories.json") is None:
        from Core.LifeRPG.categories import DEFAULT_CATEGORIES

        store.write_json("Data", "", "categories.json", {"categories": DEFAULT_CATEGORIES})
    if store.read_json("Data", "", "projects.json") is None:
        from Core.LifeRPG.projects import DEFAULT_PROJECTS

        store.write_json("Data", "", "projects.json", {"projects": DEFAULT_PROJECTS})
    if store.read_json("Workflow", ["Rewards"], "ledger.json") is None:
        store.write_json("Workflow", ["Rewards"], "ledger.json", to_record(TokenLedger()))
    _ensure_agents(store)
    _ensure_habits(store)
    _ensure_events(store)
    current = store.read_json("Workflow", ["Missions"], "current_mission.json")
    if current is None or current.get("date") != today_key():
        mission = Mission(id=make_id("mission", today_key()), date=today_key(), title="Stabilize the day and ship the next useful slice")
        store.write_json("Workflow", ["Missions"], "current_mission.json", to_record(mission))


def _ensure_agents(store) -> None:
    if store.list_records("Data", ["Agents"]):
        return
    agents = [
        Agent(id="agent_roh", name="Roh", role="Operator", hp=1250, max_hp=1250, power=18),
        Agent(id="agent_echo", name="Echo", role="Scout", hp=980, max_hp=980, power=12),
        Agent(id="agent_ward", name="Ward", role="Guard", hp=1080, max_hp=1080, power=10),
    ]
    for agent in agents:
        store.write_json("Data", ["Agents"], f"{agent.id}.json", to_record(agent))


def _ensure_habits(store) -> None:
    if store.list_records("Data", ["Habits"]):
        return
    for title, category in [
        ("Drink Water", "Body"),
        ("Eat Something", "Body"),
        ("Brush Teeth", "Body"),
        ("Move", "Body"),
        ("Review Day", "Recovery"),
    ]:
        habit = Habit(id=make_id("habit", title), title=title, category=category)
        store.write_json("Data", ["Habits"], f"{habit.id}.json", to_record(habit))


def _ensure_events(store) -> None:
    if store.list_records("Data", ["Events"]):
        return
    event = Event(id=make_id("event", "daily reset"), title="Daily Reset", starts_at=utc_now_iso(), reminder_minutes=[15, 60])
    store.write_json("Data", ["Events"], f"{event.id}.json", to_record(event))
