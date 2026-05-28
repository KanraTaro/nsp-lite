from __future__ import annotations

import re

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import InboxItem, to_record
from Core.LifeRPG.time import utc_now_iso


def split_dump(text: str) -> list[str]:
    chunks: list[str] = []
    for line in str(text).replace(";", "\n").splitlines():
        if "," in line and len(line) < 400:
            chunks.extend(line.split(","))
        else:
            chunks.append(line)
    return [re.sub(r"\s+", " ", chunk).strip(" -\t") for chunk in chunks if chunk.strip(" -\t")]


def add_text(store, text: str) -> list[dict]:
    ensure_defaults(store)
    created: list[dict] = []
    for index, raw in enumerate(split_dump(text)):
        created_at = utc_now_iso()
        inbox_id = make_id("inbox", created_at, index, raw)
        item = InboxItem(id=inbox_id, original_text=raw, text=raw, title=raw, created_at=created_at)
        record = to_record(item)
        store.write_json("Data", ["Inbox"], f"{inbox_id}.json", record)
        store.append_event("inbox_added", {"inbox_id": inbox_id, "text": raw})
        created.append(record)
    return created


def list_items(store, *, status: str | None = None) -> list[dict]:
    ensure_defaults(store)
    items = store.list_records("Data", ["Inbox"])
    if status:
        items = [item for item in items if item.get("status") == status]
    return sorted(items, key=lambda item: str(item.get("created_at", "")), reverse=True)


def get_item(store, inbox_id: str) -> dict:
    item = store.read_json("Data", ["Inbox"], f"{inbox_id}.json")
    if not isinstance(item, dict):
        raise ValueError(f"inbox item not found: {inbox_id}")
    return item


def save_item(store, item: dict) -> dict:
    store.write_json("Data", ["Inbox"], f"{item['id']}.json", item)
    return item
