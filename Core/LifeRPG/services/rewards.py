from __future__ import annotations

from Core.LifeRPG.ids import make_id
from Core.LifeRPG.models import Reward, TokenLedger, to_record
from Core.LifeRPG.time import utc_now_iso


def get_ledger(store) -> dict:
    ledger = store.read_json("Workflow", ["Rewards"], "ledger.json")
    if isinstance(ledger, dict):
        ledger.setdefault("xp_total", 0)
        ledger.setdefault("leisure_tokens", 0)
        ledger.setdefault("entries", [])
        return ledger
    return to_record(TokenLedger())


def grant(store, *, source: str, source_id: str, xp: int, tokens: int, note: str) -> dict:
    reward = Reward(
        id=make_id("reward", source, source_id, utc_now_iso()),
        source=source,
        source_id=source_id,
        created_at=utc_now_iso(),
        xp=max(0, int(xp)),
        tokens=max(0, int(tokens)),
        note=note,
    )
    ledger = get_ledger(store)
    record = to_record(reward)
    ledger["xp_total"] = int(ledger.get("xp_total", 0)) + reward.xp
    ledger["leisure_tokens"] = int(ledger.get("leisure_tokens", 0)) + reward.tokens
    ledger.setdefault("entries", []).append(record)
    store.write_json("Workflow", ["Rewards"], "ledger.json", ledger)
    store.write_json("Workflow", ["Rewards", "pending"], f"{reward.id}.json", record)
    store.append_event("reward_granted", {"reward_id": reward.id, "source": source, "xp": reward.xp, "tokens": reward.tokens})
    return record
