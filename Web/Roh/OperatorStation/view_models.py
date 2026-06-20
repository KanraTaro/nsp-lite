from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


LIVE_SNAPSHOT_MAX_AGE_SECONDS = 60
OPERATOR_CONVERSATION_TITLE = "Roh Operator Station Clip 1"


def _status_rank(value: str) -> int:
    ranks = {"ONLINE": 3, "LIVE": 3, "DEGRADED": 2, "STALE": 2, "OFFLINE": 1, "MISSING": 1}
    return ranks.get(str(value or "").upper(), 1)


def _format_age(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    if seconds < 1:
        return "just now"
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    return f"{int(seconds // 3600)}h ago"


def _skill_result_dict(result: Any) -> Dict[str, Any]:
    if hasattr(result, "as_dict"):
        return dict(result.as_dict())
    return {
        "exit_code": int(getattr(result, "exit_code", 1)),
        "stdout": str(getattr(result, "stdout", "") or ""),
        "stderr": str(getattr(result, "stderr", "") or ""),
    }


def _snippet(value: Any, *, limit: int = 520) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_dst_status(snapshot_payload: Dict[str, Any] | None, result: Any) -> Dict[str, Any]:
    skill = _skill_result_dict(result)
    payload = snapshot_payload if isinstance(snapshot_payload, dict) else {}
    ok = bool(payload.get("ok")) and int(skill.get("exit_code", 1)) == 0

    snapshot_path = str(payload.get("path", "") or "").strip()
    age_seconds: float | None = None
    age_label = "unknown"
    if snapshot_path:
        try:
            age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - Path(snapshot_path).expanduser().stat().st_mtime)
            age_label = _format_age(age_seconds)
        except OSError:
            age_seconds = None

    if not ok:
        bridge_state = "MISSING"
    elif age_seconds is not None and age_seconds > LIVE_SNAPSHOT_MAX_AGE_SECONDS:
        bridge_state = "STALE"
    else:
        bridge_state = "LIVE"

    world = payload.get("world") if isinstance(payload.get("world"), dict) else {}
    players = payload.get("players") if isinstance(payload.get("players"), list) else []
    player_names: List[str] = []
    for player in players:
        if isinstance(player, dict):
            player_names.append(str(player.get("name", "unknown") or "unknown"))

    summary = "No RohBridge snapshot found."
    if ok:
        phase = world.get("phase", "unknown")
        season = world.get("season", "unknown")
        day = world.get("day", "unknown")
        summary = f"Day {day}, {season}, {phase}. {len(player_names)} player(s)."

    return {
        "label": "DST Bridge",
        "status": bridge_state,
        "snapshot_found": ok,
        "snapshot_path": snapshot_path or "not found",
        "snapshot_age": age_label,
        "world": world,
        "players": player_names,
        "summary": summary,
        "detail": str(payload.get("director_hint", "") or skill.get("stderr", "") or "Waiting for RohBridge snapshot."),
        "skill": skill,
    }


def build_operator_view(payload: Dict[str, Any]) -> Dict[str, Any]:
    skillcli = payload.get("skillcli", {})
    rohtalk = payload.get("rohtalk", {})
    dst = payload.get("dst", {})
    voice = payload.get("voice", {})

    skillcli_status = "ONLINE" if skillcli.get("available") else "OFFLINE"
    rohtalk_status = "ONLINE" if rohtalk.get("available") else "OFFLINE"
    root_status = "ONLINE" if payload.get("repo_root") else "OFFLINE"
    python_status = "ONLINE" if payload.get("python_version") else "OFFLINE"
    voice_status = str(voice.get("status", "DEGRADED") or "DEGRADED").upper()
    dst_status = str(dst.get("status", "MISSING") or "MISSING").upper()

    core_statuses = [root_status, python_status, skillcli_status, rohtalk_status]
    if skillcli_status == "OFFLINE" or rohtalk_status == "OFFLINE":
        overall = "OFFLINE"
    elif any(_status_rank(status) < 3 for status in core_statuses):
        overall = "DEGRADED"
    else:
        overall = "ONLINE"

    cards = [
        {
            "label": "NSPL Root",
            "status": root_status,
            "value": payload.get("repo_root", "unknown"),
            "detail": "Repository root detected.",
        },
        {
            "label": "Python",
            "status": python_status,
            "value": payload.get("python_version", "unknown"),
            "detail": "Runtime serving this local cockpit.",
        },
        {
            "label": "SkillCLI",
            "status": skillcli_status,
            "value": "available" if skillcli.get("available") else "unavailable",
            "detail": skillcli.get("detail", "Tiny skill probe completed."),
        },
        {
            "label": "RohTalk",
            "status": rohtalk_status,
            "value": "available" if rohtalk.get("available") else "unavailable",
            "detail": rohtalk.get("detail", "Skill list checked for RohTalk commands."),
        },
        {
            "label": "Voice Provider",
            "status": voice_status,
            "value": voice.get("value", "not configured"),
            "detail": voice.get("detail", "Voice.Speak and SpeechNote are deferred to the next pass."),
        },
        {
            "label": "DST Bridge",
            "status": dst_status,
            "value": "snapshot found" if dst.get("snapshot_found") else "snapshot missing",
            "detail": dst.get("summary", "Waiting for RohBridge snapshot."),
        },
    ]

    return {
        "app_name": payload.get("app", "Roh.OperatorStation"),
        "app_version": payload.get("version", ""),
        "mode": "LOCAL OPERATOR",
        "overall_status": overall,
        "cards": cards,
        "dst": dst,
        "chat": payload.get("chat", default_chat_state()),
        "command_text": payload.get("command_text", ""),
        "auto_speak": bool(payload.get("auto_speak", False)),
        "listen_result": payload.get("listen_result"),
        "voice_result": payload.get("voice_result"),
        "submitted": bool(payload.get("submitted", False)),
        "action_trace": payload.get("action_trace", default_action_trace()),
        "diagnostics": payload.get("diagnostics", {}),
        "prompts": [
            "Roh, are you online?",
            "Check DST bridge",
            "Say hi in DST",
            "Warn us before night",
        ],
    }


def default_chat_state() -> Dict[str, Any]:
    return {
        "title": OPERATOR_CONVERSATION_TITLE,
        "conversation_id": "",
        "short_id": "",
        "latest_prompt": "",
        "latest_response": "",
        "updated_label": "",
        "exchanges": [],
        "error": "",
        "command_text": "",
        "auto_speak": False,
        "listen_result": None,
    }


def default_action_trace() -> Dict[str, Any]:
    return {
        "skill": "",
        "arguments": "",
        "conversation": "",
        "toolkit": "dst_director",
        "tools_enabled": True,
        "exit_code": "",
        "stdout": "",
        "stderr": "",
    }


def build_action_trace(
    *,
    skill: str,
    argv: List[str],
    result: Any,
    conversation_id: str = "",
    toolkit: str = "dst_director",
    tools_enabled: bool = True,
) -> Dict[str, Any]:
    skill_result = _skill_result_dict(result)
    return {
        "skill": skill,
        "arguments": " ".join(str(item) for item in argv[1:]),
        "conversation": conversation_id[:8] if conversation_id else "",
        "toolkit": toolkit,
        "tools_enabled": bool(tools_enabled),
        "exit_code": int(skill_result.get("exit_code", 1)),
        "stdout": _snippet(skill_result.get("stdout", "")),
        "stderr": _snippet(skill_result.get("stderr", "")),
    }
