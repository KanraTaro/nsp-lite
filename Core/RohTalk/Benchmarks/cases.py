"""Benchmark case definitions for RohTalk."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


ModeName = str


@dataclass(frozen=True)
class BenchmarkCase:
    """One benchmark prompt and its expected tool behavior."""

    case_id: str
    mode: ModeName
    prompt: str
    expected_tool_names: List[str]
    expected_arguments: Dict[str, Dict[str, object]]
    notes: str = ""
    toolkit: Optional[str] = None
    default_tools: bool = False
    live: bool = False


SMOKE_CASES: List[BenchmarkCase] = [
    BenchmarkCase(
        case_id="simple_hello",
        mode="no-tools",
        prompt="Say hi as Roh in one short sentence.",
        expected_tool_names=[],
        expected_arguments={},
    ),
    BenchmarkCase(
        case_id="character_intro",
        mode="no-tools",
        prompt="Introduce yourself as Roh in one short sentence.",
        expected_tool_names=[],
        expected_arguments={},
    ),
    BenchmarkCase(
        case_id="dst_announce_intent",
        mode="dst-director-dry",
        prompt="Say hi in DST.",
        expected_tool_names=["announce_text"],
        expected_arguments={"announce_text": {"text": str}},
        toolkit="dst_director",
        default_tools=True,
    ),
    BenchmarkCase(
        case_id="chaos_tier_intent",
        mode="dst-director-dry",
        prompt="Set chaos tier to 3.",
        expected_tool_names=["chaos_set_tier"],
        expected_arguments={"chaos_set_tier": {"chaos_tier": 3}},
        toolkit="dst_director",
        default_tools=True,
    ),
    BenchmarkCase(
        case_id="deerclops_intent",
        mode="dst-director-dry",
        prompt="Summon Deerclops.",
        expected_tool_names=["chaos_set_tier", "enemy_spawn"],
        expected_arguments={
            "chaos_set_tier": {"chaos_tier": 3},
            "enemy_spawn": {"prefab": "deerclops", "force_boss": True},
        },
        notes="Dry mode records requested tool intent and does not execute DST actions.",
        toolkit="dst_director",
        default_tools=True,
    ),
    BenchmarkCase(
        case_id="dst_announce_live",
        mode="dst-director-live",
        prompt="Say hi in DST.",
        expected_tool_names=["announce_text"],
        expected_arguments={"announce_text": {"text": str}},
        toolkit="dst_director",
        default_tools=True,
        live=True,
        notes="Requires --allow-live-dst-actions.",
    ),
    BenchmarkCase(
        case_id="deerclops_live",
        mode="dst-director-live",
        prompt="Summon Deerclops.",
        expected_tool_names=["chaos_set_tier", "enemy_spawn"],
        expected_arguments={
            "chaos_set_tier": {"chaos_tier": 3},
            "enemy_spawn": {"prefab": "deerclops", "force_boss": True},
        },
        toolkit="dst_director",
        default_tools=True,
        live=True,
        notes="Live Deerclops workflow; requires --allow-live-dst-actions and is not selected by default.",
    ),
]


DEFAULT_CASE_IDS_BY_MODE: Dict[str, List[str]] = {
    "no-tools": ["simple_hello", "character_intro"],
    "tool-dry": ["dst_announce_intent", "chaos_tier_intent", "deerclops_intent"],
    "dst-director-dry": ["dst_announce_intent", "chaos_tier_intent", "deerclops_intent"],
    "dst-director-live": ["dst_announce_live"],
}


def normalize_mode(mode: str) -> str:
    normalized = str(mode or "no-tools").strip().lower()
    if normalized not in DEFAULT_CASE_IDS_BY_MODE:
        raise ValueError(f"Unknown RohTalk benchmark mode: {mode}")
    return normalized


def get_cases(
    *,
    suite: str,
    mode: str,
    case_ids: Optional[Iterable[str]] = None,
) -> List[BenchmarkCase]:
    """Return benchmark cases for a suite and mode."""
    normalized_suite = str(suite or "smoke").strip().lower()
    normalized_mode = normalize_mode(mode)

    if normalized_suite != "smoke":
        raise ValueError(f"Unknown RohTalk benchmark suite: {suite}")

    by_id = {case.case_id: case for case in SMOKE_CASES}
    if case_ids:
        selected_ids = [str(case_id).strip() for case_id in case_ids if str(case_id).strip()]
    else:
        selected_ids = list(DEFAULT_CASE_IDS_BY_MODE[normalized_mode])

    cases: List[BenchmarkCase] = []
    for case_id in selected_ids:
        case = by_id.get(case_id)
        if case is None:
            raise ValueError(f"Unknown RohTalk benchmark case: {case_id}")
        cases.append(case)

    if not cases:
        raise ValueError(f"No benchmark cases for mode: {mode}")
    return cases
