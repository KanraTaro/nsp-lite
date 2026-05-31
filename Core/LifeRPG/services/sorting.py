from __future__ import annotations

import re

from Core.LifeRPG.categories import canonical_category
from Core.LifeRPG.defaults import ensure_defaults
from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import SortBatch, SortProposal, to_record
from Core.LifeRPG.projects import canonical_project
from Core.LifeRPG.services import inbox
from Core.LifeRPG.time import utc_now_iso


def _title(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    words = cleaned.split()
    if not words:
        return "Untitled Quest"
    return " ".join(word[:1].upper() + word[1:] for word in words[:8])


def _minimum_win(text: str, title: str) -> str:
    low = text.casefold()
    if any(word in low for word in ["call", "email", "message"]):
        return f"Send or complete the first contact for {title}."
    if any(word in low for word in ["fix", "build", "code", "pass", "page"]):
        return f"Make one visible improvement to {title}."
    if any(word in low for word in ["clean", "laundry", "dishes", "tidy"]):
        return f"Finish one clear cleanup step for {title}."
    return f"Move {title} forward for 10 minutes."


def _energy(text: str) -> int:
    low = text.casefold()
    score = 2
    if any(word in low for word in ["quick", "water", "brush", "text"]):
        score -= 1
    if any(word in low for word in ["deep", "build", "fix", "paperwork", "client", "dad"]):
        score += 2
    return max(1, min(5, score))


def _priority(text: str, category: str) -> int:
    low = text.casefold()
    if any(word in low for word in ["urgent", "today", "dad", "bill", "paperwork"]):
        return 5
    if category in {"Survival", "Family", "Admin"}:
        return 4
    return 3


def sort_inbox(store, *, status: str = "raw") -> dict:
    ensure_defaults(store)
    raw_items = [item for item in inbox.list_items(store) if item.get("status") == status]
    batch_id = make_id("sort", utc_now_iso(), len(raw_items))
    batch = SortBatch(id=batch_id, created_at=utc_now_iso(), status="accepted")
    proposals: list[dict] = []
    for item in raw_items:
        original = item.get("original_text") or item.get("text") or ""
        title = _title(original)
        category = canonical_category(None, text=original)
        project = canonical_project(None, text=original)
        proposal = SortProposal(
            id=make_id("proposal", batch_id, item["id"]),
            inbox_id=item["id"],
            original_text=original,
            title=title,
            project=project,
            category=category,
            minimum_win=_minimum_win(original, title),
            energy_cost=_energy(original),
            priority=_priority(original, category),
        )
        item["previous_state"] = {k: item.get(k) for k in ["status", "title", "project", "category", "minimum_win", "energy_cost", "priority", "quest_id"]}
        item.update(
            {
                "status": "sorted",
                "title": proposal.title,
                "project": proposal.project,
                "category": proposal.category,
                "minimum_win": proposal.minimum_win,
                "energy_cost": proposal.energy_cost,
                "priority": proposal.priority,
                "sort_batch_id": batch_id,
                "original_text": original,
            }
        )
        inbox.save_item(store, item)
        proposal_record = to_record(proposal)
        store.write_json("Workflow", ["Roh", "proposals"], f"{proposal.id}.json", proposal_record)
        proposals.append(proposal_record)
        batch.inbox_ids.append(item["id"])
        batch.proposal_ids.append(proposal.id)
    batch_record = to_record(batch)
    store.write_json("Workflow", ["Roh", "sort_batches"], f"{batch_id}.json", batch_record)
    store.append_event("roh_sort_completed", {"batch_id": batch_id, "count": len(proposals)}, roh=True)
    return {"batch": batch_record, "proposals": proposals, "items": [inbox.get_item(store, item_id) for item_id in batch.inbox_ids]}


def revert_item(store, inbox_id: str) -> dict:
    item = inbox.get_item(store, inbox_id)
    previous = item.get("previous_state")
    if not isinstance(previous, dict):
        raise ValueError(f"inbox item has no previous state: {inbox_id}")
    for key, value in previous.items():
        item[key] = value
    item["previous_state"] = None
    item["status"] = previous.get("status") or "raw"
    inbox.save_item(store, item)
    store.append_event("roh_sort_item_reverted", {"inbox_id": inbox_id}, roh=True)
    return item


def revert_batch(store, batch_id: str) -> list[dict]:
    batch = store.read_json("Workflow", ["Roh", "sort_batches"], f"{batch_id}.json")
    if not isinstance(batch, dict):
        raise ValueError(f"sort batch not found: {batch_id}")
    reverted = [revert_item(store, item_id) for item_id in batch.get("inbox_ids", [])]
    batch["status"] = "reverted"
    store.write_json("Workflow", ["Roh", "sort_batches"], f"{batch_id}.json", batch)
    return reverted
