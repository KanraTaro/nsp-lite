from __future__ import annotations

from Core.LifeRPG.defaults import ensure_defaults


def list_events(store) -> list[dict]:
    ensure_defaults(store)
    return store.list_records("Data", ["Events"])
