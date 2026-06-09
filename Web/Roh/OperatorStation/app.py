from __future__ import annotations

import json
import platform
from pathlib import Path
from urllib.parse import parse_qs
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from Web.Roh.OperatorStation.view_models import (
    OPERATOR_CONVERSATION_TITLE,
    build_action_trace,
    build_dst_status,
    build_operator_view,
    default_action_trace,
    default_chat_state,
)


def _parse_json_result(result: Any) -> tuple[Dict[str, Any] | None, str | None]:
    if int(getattr(result, "exit_code", 1)) != 0:
        return None, str(getattr(result, "stderr", "") or "skill returned a non-zero exit code")

    try:
        payload = json.loads(str(getattr(result, "stdout", "") or "{}"))
    except Exception as exc:
        return None, f"could not parse skill JSON: {exc}"

    if isinstance(payload, dict):
        return payload, None
    return None, "skill JSON root was not an object"


def _parse_json_stdout(result: Any) -> Dict[str, Any] | None:
    try:
        payload = json.loads(str(getattr(result, "stdout", "") or "{}"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _result_dict(result: Any) -> Dict[str, Any]:
    if hasattr(result, "as_dict"):
        return dict(result.as_dict())
    return {
        "exit_code": int(getattr(result, "exit_code", 1)),
        "stdout": str(getattr(result, "stdout", "") or ""),
        "stderr": str(getattr(result, "stderr", "") or ""),
    }


def _parse_conversation_list(stdout: str) -> list[Dict[str, str]]:
    conversations: list[Dict[str, str]] = []
    for raw_line in str(stdout or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("[") or "]" not in line:
            continue
        try:
            index_text, rest = line[1:].split("]", 1)
            parts = [part.strip() for part in rest.strip().split("|")]
        except ValueError:
            continue
        if len(parts) < 4:
            continue
        conversations.append(
            {
                "index": index_text.strip(),
                "title": parts[0],
                "short_id": parts[1],
                "updated_at": parts[2],
                "id": parts[3],
            }
        )
    return conversations


def _find_operator_conversation(context: Any) -> Dict[str, str] | None:
    result = context.run_skill(["RohTalk.list_conversations"], timeout=5.0)
    if int(getattr(result, "exit_code", 1)) != 0:
        return None

    matches = [
        item for item in _parse_conversation_list(str(getattr(result, "stdout", "") or ""))
        if item.get("title") == OPERATOR_CONVERSATION_TITLE and item.get("id")
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda item: item.get("updated_at", ""))[-1]


def _parse_start_conversation_id(stdout: str) -> str:
    for line in str(stdout or "").splitlines():
        if line.startswith("conversation_id:"):
            return line.split(":", 1)[1].strip()
    return ""


def _extract_roh_reply(stdout: str, *, started: bool) -> str:
    lines = str(stdout or "").splitlines()
    if started:
        lines = [
            line for line in lines
            if not line.startswith("conversation_id:") and not line.startswith("title:")
        ]
    return "\n".join(lines).strip()


def _chat_state_from_conversation(conversation: Dict[str, str] | None) -> Dict[str, Any]:
    chat = default_chat_state()
    if conversation:
        conversation_id = conversation.get("id", "")
        chat.update(
            {
                "conversation_id": conversation_id,
                "short_id": conversation.get("short_id", conversation_id[:8]),
            }
        )
    return chat


def _load_rohtalk_diagnostics(context: Any) -> Dict[str, Any]:
    config_path = Path(context.repo_root) / "Config" / "RohTalk" / "config.json"
    result = {
        "toolkit": "dst_director",
        "tools_enabled": True,
        "chat_timeout": 180,
        "model": "",
        "profile": "",
    }
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return result
    if isinstance(payload, dict):
        result["model"] = str(payload.get("default_model", "") or "")
        profiles = payload.get("profiles", {})
        if isinstance(profiles, dict) and "dst_director_fast" in profiles:
            result["profile"] = "dst_director_fast"
    return result


async def _form_values(request: Request) -> Dict[str, str]:
    try:
        raw = (await request.body()).decode("utf-8", errors="replace")
        values = parse_qs(raw, keep_blank_values=True)
        if values:
            return {key: str(items[-1]).strip() for key, items in values.items() if items}
    except Exception:
        pass
    try:
        form = await request.form()
    except Exception:
        return {}
    return {str(key): str(value).strip() for key, value in form.items()}


def _run_voice_speak(context: Any, text: str, conversation_id: str = "") -> tuple[Dict[str, Any], Dict[str, Any]]:
    argv = ["Voice.Speak", "--provider", "speechnote", "--text", text, "--json"]
    result = context.run_skill(argv, timeout=20.0)
    voice_result = _parse_json_stdout(result) or {
        "ok": False,
        "stderr": str(getattr(result, "stderr", "") or "Voice.Speak failed."),
        "provider": "speechnote",
    }
    trace = build_action_trace(
        skill="Voice.Speak",
        argv=argv,
        result=result,
        conversation_id=conversation_id,
        toolkit="none",
        tools_enabled=False,
    )
    return voice_result, trace


def _run_roh_turn(context: Any, prompt: str) -> Dict[str, Any]:
    existing = _find_operator_conversation(context)
    started = existing is None

    if started:
        argv = [
            "RohTalk.start",
            "--title",
            OPERATOR_CONVERSATION_TITLE,
            "--tools",
            "--toolkit",
            "dst_director",
            "--",
            prompt,
        ]
        result = context.run_skill(argv, timeout=180.0)
        conversation_id = _parse_start_conversation_id(str(getattr(result, "stdout", "") or ""))
        short_id = conversation_id[:8]
    else:
        conversation_id = str(existing.get("id", ""))
        short_id = str(existing.get("short_id", conversation_id[:8]))
        argv = [
            "RohTalk.chat",
            "--tools",
            "--toolkit",
            "dst_director",
            "--tool-trace",
            conversation_id,
            "--",
            prompt,
        ]
        result = context.run_skill(argv, timeout=180.0)

    reply = _extract_roh_reply(str(getattr(result, "stdout", "") or ""), started=started)
    chat = {
        "title": OPERATOR_CONVERSATION_TITLE,
        "conversation_id": conversation_id,
        "short_id": short_id,
        "latest_prompt": prompt,
        "latest_response": reply,
        "exchanges": [{"user": prompt, "assistant": reply}] if reply else [],
        "updated_label": "Updated just now" if reply else "",
        "error": "" if int(getattr(result, "exit_code", 1)) == 0 else str(getattr(result, "stderr", "") or "RohTalk turn failed."),
    }

    return {
        "chat": chat,
        "action_trace": build_action_trace(
            skill=argv[0],
            argv=argv,
            result=result,
            conversation_id=conversation_id,
            toolkit="dst_director",
            tools_enabled=True,
        ),
    }


def _load_operator_payload(
    context: Any,
    *,
    chat: Dict[str, Any] | None = None,
    action_trace: Dict[str, Any] | None = None,
    voice_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    time_result = context.run_skill(["NSPL.Tools.Time.now", "--json"], timeout=4.0)
    _time_payload, time_error = _parse_json_result(time_result)
    skillcli_available = int(getattr(time_result, "exit_code", 1)) == 0 and time_error is None

    list_result = context.run_skill(["list"], timeout=4.0)
    skill_list = str(getattr(list_result, "stdout", "") or "")
    rohtalk_available = int(getattr(list_result, "exit_code", 1)) == 0 and "RohTalk.start" in skill_list

    dst_result = context.run_skill(["Game.DST.Snapshot.read", "--json"], timeout=5.0)
    dst_payload, _dst_error = _parse_json_result(dst_result)
    dst_status = build_dst_status(dst_payload, dst_result)

    voice_check = context.run_skill(["Voice.Speak", "--check", "--provider", "speechnote", "--json"], timeout=5.0)
    voice_payload = _parse_json_stdout(voice_check) or {}
    voice_available = bool(voice_payload.get("ok")) and int(getattr(voice_check, "exit_code", 1)) == 0
    listen_available = "Voice.Listen" in skill_list

    active_conversation = _find_operator_conversation(context)
    chat_state = chat or _chat_state_from_conversation(active_conversation)
    command_text = str((chat_state or {}).get("command_text", "") or "")

    voice_detail = (
        "Local SpeechNote Flatpak provider is available for speech and clipboard listening."
        if voice_available and listen_available
        else str(voice_payload.get("stderr", "") or "SpeechNote or Voice.Listen is unavailable.")
    )
    if voice_available and not listen_available:
        voice_detail = "SpeechNote is available, but Voice.Listen is not registered."

    payload: Dict[str, Any] = {
        "app": context.metadata.get("name", "Roh.OperatorStation"),
        "version": context.metadata.get("version", ""),
        "repo_root": str(context.repo_root),
        "python_version": platform.python_version(),
        "skillcli": {
            "available": skillcli_available,
            "detail": "NSPL.Tools.Time.now probe succeeded." if skillcli_available else time_error or "SkillCLI probe failed.",
            "result": _result_dict(time_result),
        },
        "rohtalk": {
            "available": rohtalk_available,
            "detail": "RohTalk skills are registered." if rohtalk_available else "RohTalk skills were not found in skill list.",
            "result": _result_dict(list_result),
        },
        "voice": {
            "status": "ONLINE" if voice_available and listen_available else "DEGRADED",
            "value": "SpeechNote" if voice_available else "not configured",
            "detail": voice_detail,
            "result": _result_dict(voice_check),
        },
        "dst": dst_status,
        "chat": chat_state,
        "command_text": command_text,
        "auto_speak": bool((chat_state or {}).get("auto_speak", False)),
        "listen_result": (chat_state or {}).get("listen_result"),
        "action_trace": action_trace or default_action_trace(),
        "voice_result": voice_result,
        "diagnostics": _load_rohtalk_diagnostics(context),
    }
    payload["ui"] = build_operator_view(payload)
    return payload


def create_app(context: Any) -> FastAPI:
    app_dir = Path(context.app_dir)
    templates = Jinja2Templates(directory=str(app_dir / "templates"))

    app = FastAPI(title="Roh Operator Station")
    app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"ok": True, "app": context.metadata.get("name", "Roh.OperatorStation")}

    @app.get("/api/status", response_class=JSONResponse)
    async def api_status() -> Dict[str, Any]:
        return _load_operator_payload(context)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        payload = _load_operator_payload(context)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                **payload,
            },
        )

    @app.post("/send", response_class=HTMLResponse)
    async def send(request: Request):
        values = await _form_values(request)
        prompt = str(values.get("demo_prompt") or values.get("prompt", "") or "").strip()
        auto_speak = str(values.get("auto_speak", "")).lower() in {"1", "true", "on", "yes"}
        if prompt == "":
            chat = default_chat_state()
            chat["error"] = "Enter a prompt before sending."
            chat["command_text"] = str(values.get("prompt", "") or "")
            chat["auto_speak"] = auto_speak
            payload = _load_operator_payload(context, chat=chat)
        else:
            turn = _run_roh_turn(context, prompt)
            turn["chat"]["auto_speak"] = auto_speak
            if turn["chat"].get("error"):
                turn["chat"]["command_text"] = prompt
            else:
                turn["chat"]["command_text"] = ""

            voice_result = None
            payload = _load_operator_payload(
                context,
                chat=turn["chat"],
                action_trace=turn["action_trace"],
            )
            if auto_speak and turn["chat"].get("latest_response") and not turn["chat"].get("error"):
                voice_result, _voice_trace = _run_voice_speak(
                    context,
                    str(turn["chat"].get("latest_response", "")),
                    str(turn["chat"].get("conversation_id", "")),
                )
                payload = _load_operator_payload(
                    context,
                    chat=turn["chat"],
                    action_trace=turn["action_trace"],
                    voice_result=voice_result,
                )
        return templates.TemplateResponse(request, "index.html", {**payload})

    @app.post("/speak", response_class=HTMLResponse)
    async def speak(request: Request):
        values = await _form_values(request)
        text = str(values.get("response_text", "") or "").strip()
        chat = default_chat_state()
        chat["latest_prompt"] = str(values.get("latest_prompt", "") or "").strip()
        chat["latest_response"] = text
        chat["conversation_id"] = str(values.get("conversation_id", "") or "").strip()
        chat["short_id"] = chat["conversation_id"][:8]

        if text == "":
            voice_result = {"ok": False, "stderr": "No Roh response is available to speak.", "provider": "speechnote"}
            trace = default_action_trace()
        else:
            voice_result, trace = _run_voice_speak(context, text, chat["conversation_id"])

        payload = _load_operator_payload(context, chat=chat, action_trace=trace, voice_result=voice_result)
        return templates.TemplateResponse(request, "index.html", {**payload})

    @app.post("/listen", response_class=HTMLResponse)
    async def listen(request: Request):
        values = await _form_values(request)
        chat = default_chat_state()
        chat["latest_prompt"] = str(values.get("latest_prompt", "") or "").strip()
        chat["latest_response"] = str(values.get("response_text", "") or "").strip()
        chat["conversation_id"] = str(values.get("conversation_id", "") or "").strip()
        chat["short_id"] = chat["conversation_id"][:8]
        chat["auto_speak"] = str(values.get("auto_speak", "")).lower() in {"1", "true", "on", "yes"}

        argv = ["Voice.Listen", "--provider", "speechnote", "--timeout", "20", "--json"]
        result = context.run_skill(argv, timeout=30.0)
        listen_result = _parse_json_stdout(result) or {
            "ok": False,
            "provider": "speechnote",
            "transcript": "",
            "method": "clipboard",
            "error": str(getattr(result, "stderr", "") or "Voice.Listen failed."),
        }
        if not bool(listen_result.get("ok")) and str(listen_result.get("error", "") or "").strip() == "":
            listen_result["error"] = "No new SpeechNote transcript detected."
        transcript = str(listen_result.get("transcript", "") or "").strip() if bool(listen_result.get("ok")) else ""
        chat["command_text"] = transcript or str(values.get("prompt", "") or "").strip()
        chat["listen_result"] = listen_result
        trace = build_action_trace(
            skill="Voice.Listen",
            argv=argv,
            result=result,
            conversation_id=chat["conversation_id"],
            toolkit="none",
            tools_enabled=False,
        )
        payload = _load_operator_payload(context, chat=chat, action_trace=trace)
        return templates.TemplateResponse(request, "index.html", {**payload})

    return app
