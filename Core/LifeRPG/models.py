from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def to_record(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return dict(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


@dataclass
class ProfileSettings:
    display_name: str = "Operator"
    timezone: str = "UTC"
    default_scope: str = "Global"


@dataclass
class InboxItem:
    id: str
    original_text: str
    text: str
    created_at: str
    status: str = "raw"
    title: str = ""
    project: str = "General"
    category: str = "Survival"
    minimum_win: str = ""
    energy_cost: int = 1
    priority: int = 3
    quest_id: str | None = None
    sort_batch_id: str | None = None
    previous_state: dict[str, Any] | None = None
    updated_at: str | None = None


@dataclass
class SortProposal:
    id: str
    inbox_id: str
    original_text: str
    title: str
    project: str
    category: str
    minimum_win: str
    energy_cost: int
    priority: int
    status: str = "accepted"


@dataclass
class SortBatch:
    id: str
    created_at: str
    status: str
    inbox_ids: list[str] = field(default_factory=list)
    proposal_ids: list[str] = field(default_factory=list)


@dataclass
class QuestStep:
    title: str
    status: str = "open"


@dataclass
class Quest:
    id: str
    title: str
    original_text: str
    project: str
    category: str
    status: str
    created_at: str
    minimum_win: str = ""
    energy_cost: int = 1
    priority: int = 3
    inbox_id: str | None = None
    active_session_id: str | None = None
    completed_at: str | None = None
    archived_at: str | None = None
    notes: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class QuestSession:
    id: str
    quest_id: str
    started_at: str
    status: str = "active"
    ended_at: str | None = None
    note: str = ""
    pause_reason: str = ""
    last_checkin_at: str | None = None
    next_checkin_due_at: str | None = None
    stale_after_minutes: int = 90
    expedition_id: str | None = None


@dataclass
class Mission:
    id: str
    date: str
    title: str
    status: str = "active"
    focus: str = "Turn the messy day into playable missions."


@dataclass
class Habit:
    id: str
    title: str
    category: str
    cadence: str = "daily"
    status: str = "open"
    streak: int = 0
    tally: int = 0
    last_checked_at: str | None = None


@dataclass
class Event:
    id: str
    title: str
    starts_at: str | None = None
    ends_at: str | None = None
    status: str = "scheduled"
    reminder_minutes: list[int] = field(default_factory=lambda: [15])
    notes: str = ""


@dataclass
class Agent:
    id: str
    name: str
    role: str
    hp: int
    max_hp: int
    power: int


@dataclass
class Threat:
    id: str
    name: str
    hp: int
    max_hp: int
    power: int


@dataclass
class Expedition:
    id: str
    quest_id: str
    session_id: str
    status: str
    created_at: str
    progress: int = 0
    ticks: int = 0
    allies: list[dict[str, Any]] = field(default_factory=list)
    enemies: list[dict[str, Any]] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    resolved_at: str | None = None


@dataclass
class Reward:
    id: str
    source: str
    source_id: str
    created_at: str
    xp: int = 0
    tokens: int = 0
    note: str = ""


@dataclass
class TokenLedger:
    xp_total: int = 0
    leisure_tokens: int = 0
    entries: list[dict[str, Any]] = field(default_factory=list)
