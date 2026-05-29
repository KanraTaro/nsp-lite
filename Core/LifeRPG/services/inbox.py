from __future__ import annotations

import re

from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.categories import canonical_category
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


def list_items(store, *, status: str | None = None, include_archived: bool = False) -> list[dict]:
    ensure_defaults(store)
    items = store.list_records("Data", ["Inbox"])
    if not include_archived and status is None:
        items = [item for item in items if item.get("status") not in {"archived", "deleted"}]
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


def edit_item(
    store,
    inbox_id: str,
    *,
    title: str | None = None,
    text: str | None = None,
    category: str | None = None,
    minimum_win: str | None = None,
    priority: int | str | None = None,
    energy_cost: int | str | None = None,
) -> dict:
    ensure_defaults(store)
    item = get_item(store, inbox_id)
    if title is not None:
        item["title"] = str(title).strip() or item.get("title") or item.get("original_text") or "Untitled"
    if text is not None:
        item["text"] = str(text).strip()
    if category is not None:
        item["category"] = canonical_category(category, text=item.get("original_text") or item.get("text") or "")
    if minimum_win is not None:
        item["minimum_win"] = str(minimum_win).strip()
    if priority is not None and str(priority).strip():
        item["priority"] = max(1, min(5, int(priority)))
    if energy_cost is not None and str(energy_cost).strip():
        item["energy_cost"] = max(1, min(5, int(energy_cost)))
    item["updated_at"] = utc_now_iso()
    save_item(store, item)
    store.append_event("inbox_edited", {"inbox_id": inbox_id})
    return item


def archive_item(store, inbox_id: str, *, delete: bool = False) -> dict:
    ensure_defaults(store)
    item = get_item(store, inbox_id)
    item["status"] = "deleted" if delete else "archived"
    item["archived_at"] = utc_now_iso()
    save_item(store, item)
    store.append_event("inbox_deleted" if delete else "inbox_archived", {"inbox_id": inbox_id})
    return item
