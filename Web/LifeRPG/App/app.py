from __future__ import annotations

from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import json
from urllib.parse import parse_qs


def clean_text(value: str | None) -> str:
    return str(value or "").strip()


def parse_skill_json(result) -> dict:
    if result.exit_code != 0:
        return {"ok": False, "error": result.stderr or "skill failed", "result": result.as_dict()}
    try:
        payload = json.loads(result.stdout or "{}")
    except Exception as exc:
        return {"ok": False, "error": f"could not parse skill JSON: {exc}", "result": result.as_dict()}
    if isinstance(payload, dict):
        payload["ok"] = True
        return payload
    return {"ok": True, "value": payload}


def _skill(context, argv: list[str]) -> dict:
    return parse_skill_json(context.run_skill([*argv, "--json"]))


def _format_event_time(value: object) -> str:
    text = clean_text(str(value)) if value is not None else ""
    if not text:
        return "Unscheduled"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.strftime("%b %-d, %-I:%M %p")


def _decorate_board_payload(payload: dict) -> dict:
    events = payload.get("events", [])
    if isinstance(events, list):
        decorated_events: list[dict] = []
        for event in events:
            if isinstance(event, dict):
                item = dict(event)
                item["display_time"] = _format_event_time(item.get("starts_at"))
                decorated_events.append(item)
            else:
                decorated_events.append(event)
        payload["events"] = decorated_events
    return payload


def _board_payload(context) -> dict:
    payload = _skill(context, ["LifeRPG.Mission.Status"])
    if not payload.get("ok"):
        payload = {
            "mission": {},
            "habits": [],
            "events": [],
            "quests": [],
            "inbox": [],
            "ledger": {},
            "active": None,
            "error": payload.get("error"),
        }
    return _decorate_board_payload(payload)


def create_app(context):
    app_dir = Path(context.app_dir)
    templates = Jinja2Templates(directory=str(app_dir / "templates"))
    app = FastAPI(title="LifeRPG Command Center")
    app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")

    def render(request: Request, template: str, extra: dict | None = None):
        payload = _board_payload(context)
        data = {"request": request, **payload}
        if extra:
            data.update(extra)
        return templates.TemplateResponse(template, data)

    async def form_value(request: Request, name: str) -> str:
        try:
            raw = (await request.body()).decode("utf-8", errors="replace")
            values = parse_qs(raw, keep_blank_values=True)
            if name in values and values[name]:
                return clean_text(values[name][0])
        except Exception:
            pass
        try:
            form = await request.form()
        except Exception:
            return ""
        return clean_text(form.get(name))

    @app.get("/health")
    async def health():
        return {"ok": True, "app": context.metadata.get("name", "LifeRPG.App")}

    @app.get("/api/board", response_class=JSONResponse)
    async def api_board():
        return _board_payload(context)

    @app.get("/", response_class=HTMLResponse)
    async def board(request: Request):
        return render(request, "board.html")

    @app.get("/inbox", response_class=HTMLResponse)
    async def inbox_page(request: Request):
        return render(request, "inbox.html")

    @app.get("/quests", response_class=HTMLResponse)
    async def quests_page(request: Request):
        return render(request, "quests.html")

    @app.get("/today", response_class=HTMLResponse)
    async def today_page(request: Request):
        return render(request, "today.html")

    @app.get("/roh", response_class=HTMLResponse)
    async def roh_page(request: Request):
        return render(request, "roh.html")

    @app.post("/quick-dump", response_class=HTMLResponse)
    async def quick_dump(request: Request):
        text = await form_value(request, "text")
        if text:
            _skill(context, ["LifeRPG.Inbox.Add", "--text", text])
        return render(request, "partials/inbox_items.html")

    @app.post("/sort", response_class=HTMLResponse)
    async def sort(request: Request):
        _skill(context, ["LifeRPG.Inbox.Sort"])
        return render(request, "partials/inbox_items.html")

    @app.post("/quest/start", response_class=HTMLResponse)
    async def start_quest(request: Request):
        inbox_id = await form_value(request, "inbox_id")
        quest_id = await form_value(request, "quest_id")
        if inbox_id:
            _skill(context, ["LifeRPG.Quest.Start", "--inbox-id", inbox_id])
        elif quest_id:
            _skill(context, ["LifeRPG.Quest.Start", "--quest-id", quest_id])
        return render(request, "partials/active_session.html")

    @app.post("/quest/pause", response_class=HTMLResponse)
    async def pause_quest(request: Request):
        quest_id = await form_value(request, "quest_id")
        note = await form_value(request, "note")
        if quest_id:
            _skill(context, ["LifeRPG.Quest.Pause", "--quest-id", quest_id, "--note", clean_text(note)])
        return render(request, "partials/active_session.html")

    @app.post("/quest/complete", response_class=HTMLResponse)
    async def complete_quest(request: Request):
        quest_id = await form_value(request, "quest_id")
        note = await form_value(request, "note")
        if quest_id:
            _skill(context, ["LifeRPG.Quest.Complete", "--quest-id", quest_id, "--note", clean_text(note)])
        return render(request, "partials/active_session.html")

    @app.post("/habit/check", response_class=HTMLResponse)
    async def check_habit(request: Request):
        habit_id = await form_value(request, "habit_id")
        if habit_id:
            _skill(context, ["LifeRPG.Habit.Check", "--habit-id", habit_id])
        return render(request, "partials/habit_list.html")

    @app.post("/expedition/tick", response_class=HTMLResponse)
    async def expedition_tick(request: Request):
        payload = _board_payload(context)
        active = payload.get("active") or {}
        exp = active.get("expedition") or {}
        if exp.get("id"):
            _skill(context, ["LifeRPG.Expedition.Tick", "--expedition-id", exp["id"]])
        return render(request, "partials/expedition.html")

    @app.get("/partials/{name}", response_class=HTMLResponse)
    async def partial(request: Request, name: str):
        allowed = {
            "operator": "partials/operator_card.html",
            "mission": "partials/mission_card.html",
            "quick-dump": "partials/quick_dump.html",
            "active-session": "partials/active_session.html",
            "expedition": "partials/expedition.html",
            "inbox-items": "partials/inbox_items.html",
            "habits": "partials/habit_list.html",
            "events": "partials/event_list.html",
            "rewards": "partials/reward_panel.html",
            "roh": "partials/roh_proposals.html",
        }
        template = allowed.get(name)
        if not template:
            return RedirectResponse("/")
        return render(request, template)

    return app
