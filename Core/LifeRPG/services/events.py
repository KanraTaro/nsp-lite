from __future__ import annotations

from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Event, to_record
from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.time import utc_now_iso


def list_events(store, *, include_archived: bool = False) -> list[dict]:
    ensure_defaults(store)
    events = store.list_records("Data", ["Events"])
    if not include_archived:
        events = [event for event in events if event.get("status") not in {"archived", "deleted"}]
    return sorted(events, key=lambda event: str(event.get("starts_at") or event.get("created_at") or ""))


def parse_reminders(value: str | list[int] | None) -> list[int]:
    if isinstance(value, list):
        return [int(item) for item in value]
    if not value:
        return [15]
    reminders: list[int] = []
    for part in str(value).replace(";", ",").split(","):
        cleaned = part.strip()
        if cleaned:
            reminders.append(int(cleaned))
    return reminders or [15]


def create(
    store,
    title: str,
    *,
    starts_at: str | None = None,
    ends_at: str | None = None,
    reminder_minutes: str | list[int] | None = None,
    status: str = "scheduled",
    notes: str = "",
) -> dict:
    ensure_defaults(store)
    clean_title = title.strip() or "Untitled Event"
    event = Event(
        id=make_id("event", utc_now_iso(), clean_title),
        title=clean_title,
        starts_at=starts_at or None,
        ends_at=ends_at or None,
        status=status or "scheduled",
        reminder_minutes=parse_reminders(reminder_minutes),
        notes=notes,
    )
    record = to_record(event)
    record["created_at"] = utc_now_iso()
    store.write_json("Data", ["Events"], f"{event.id}.json", record)
    store.append_event("event_created", {"event_id": event.id})
    return record


def get_event(store, event_id: str) -> dict:
    event = store.read_json("Data", ["Events"], f"{event_id}.json")
    if not isinstance(event, dict):
        raise ValueError(f"event not found: {event_id}")
    return event


def edit(
    store,
    event_id: str,
    *,
    title: str | None = None,
    starts_at: str | None = None,
    ends_at: str | None = None,
    reminder_minutes: str | list[int] | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict:
    event = get_event(store, event_id)
    if title is not None:
        event["title"] = str(title).strip() or event.get("title") or "Untitled Event"
    if starts_at is not None:
        event["starts_at"] = starts_at or None
    if ends_at is not None:
        event["ends_at"] = ends_at or None
    if reminder_minutes is not None:
        event["reminder_minutes"] = parse_reminders(reminder_minutes)
    if status is not None:
        event["status"] = status or "scheduled"
    if notes is not None:
        event["notes"] = notes
    event["updated_at"] = utc_now_iso()
    store.write_json("Data", ["Events"], f"{event_id}.json", event)
    store.append_event("event_edited", {"event_id": event_id})
    return event


def archive(store, event_id: str, *, delete: bool = False) -> dict:
    event = get_event(store, event_id)
    event["status"] = "deleted" if delete else "archived"
    event["archived_at"] = utc_now_iso()
    store.write_json("Data", ["Events"], f"{event_id}.json", event)
    store.append_event("event_deleted" if delete else "event_archived", {"event_id": event_id})
    return event
