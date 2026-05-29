from __future__ import annotations

from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import json
from urllib.parse import parse_qs

from Web.LifeRPG.App.ui_choices import all_choices
from Web.LifeRPG.App.view_models import board_view_model


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

    def _request_page(request: Request, fallback: str = "board") -> str:
        headers = getattr(request, "headers", {}) or {}
        current = ""
        try:
            current = headers.get("HX-Current-URL") or headers.get("hx-current-url") or headers.get("referer") or ""
        except AttributeError:
            current = ""
        path = str(getattr(request, "scope", {}).get("path", ""))
        marker = f"{current} {path}"
        for page in ("inbox", "quests", "today", "settings", "roh"):
            if f"/{page}" in marker:
                return page
        return fallback

    def render(request: Request, template: str, extra: dict | None = None):
        payload = _board_payload(context)
        page = (extra or {}).get("page") or _request_page(request)
        data = {
            "request": request,
            "choices": all_choices(),
            "ui": board_view_model(payload, page=page),
            **payload,
        }
        if extra:
            data.update(extra)
        return templates.TemplateResponse(request, template, data)

    def render_fragment(
        request: Request,
        main_template: str,
        *,
        extra: dict | None = None,
        oob_templates: list[str] | None = None,
    ):
        merged = {"main_template": main_template, "oob_templates": oob_templates or []}
        if extra:
            merged.update(extra)
        return render(request, "partials/fragment.html", merged)

    async def form_values(request: Request) -> dict[str, str]:
        try:
            raw = (await request.body()).decode("utf-8", errors="replace")
            values = parse_qs(raw, keep_blank_values=True)
            if values:
                return {key: clean_text(items[-1]) for key, items in values.items() if items}
        except Exception:
            pass
        try:
            form = await request.form()
        except Exception:
            return {}
        return {str(key): clean_text(value) for key, value in form.items()}

    async def form_value(request: Request, name: str) -> str:
        return (await form_values(request)).get(name, "")

    @app.get("/health")
    async def health():
        return {"ok": True, "app": context.metadata.get("name", "LifeRPG.App")}

    @app.get("/api/board", response_class=JSONResponse)
    async def api_board():
        return _board_payload(context)

    @app.get("/", response_class=HTMLResponse)
    async def board(request: Request):
        return render(request, "board.html", {"page": "board"})

    @app.get("/inbox", response_class=HTMLResponse)
    async def inbox_page(request: Request):
        return render(request, "inbox.html", {"page": "inbox"})

    @app.get("/quests", response_class=HTMLResponse)
    async def quests_page(request: Request):
        return render(request, "quests.html", {"page": "quests"})

    @app.get("/today", response_class=HTMLResponse)
    async def today_page(request: Request):
        return render(request, "today.html", {"page": "today"})

    @app.get("/roh", response_class=HTMLResponse)
    async def roh_page(request: Request):
        return render(request, "roh.html", {"page": "roh"})

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        return render(request, "settings.html", {"page": "settings"})

    @app.post("/quick-dump", response_class=HTMLResponse)
    async def quick_dump(request: Request):
        text = await form_value(request, "text")
        if text:
            before = _board_payload(context)
            _skill(context, ["LifeRPG.Inbox.Add", "--text", text])
            if (before.get("settings") or {}).get("auto_sort_enabled"):
                _skill(context, ["LifeRPG.Inbox.Sort"])
                return render_fragment(
                    request,
                    "partials/inbox_items.html",
                    extra={"notice": "Captured and auto-sorted inbox item."},
                    oob_templates=["partials/roh_proposals.html"],
                )
            return render_fragment(
                request,
                "partials/inbox_items.html",
                extra={"notice": "Captured inbox item."},
                oob_templates=["partials/roh_proposals.html"],
            )
        return render(request, "partials/inbox_items.html", {"notice": "Add text before capturing."})

    @app.post("/sort", response_class=HTMLResponse)
    async def sort(request: Request):
        _skill(context, ["LifeRPG.Inbox.Sort"])
        return render_fragment(
            request,
            "partials/inbox_items.html",
            extra={"notice": "Roh sort proposal applied."},
            oob_templates=["partials/roh_proposals.html"],
        )

    @app.post("/inbox/edit", response_class=HTMLResponse)
    async def edit_inbox(request: Request):
        values = await form_values(request)
        inbox_id = values.get("inbox_id", "")
        if inbox_id:
            argv = ["LifeRPG.Inbox.Edit", "--inbox-id", inbox_id]
            for field, flag in (
                ("title", "--title"),
                ("text", "--text"),
                ("category", "--category"),
                ("minimum_win", "--minimum-win"),
                ("priority", "--priority"),
                ("energy_cost", "--energy-cost"),
            ):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/inbox_items.html", {"notice": "Inbox item updated.", "page": "inbox"})
        return render(request, "partials/inbox_items.html", {"notice": "Inbox item missing.", "page": "inbox"})

    @app.post("/inbox/archive", response_class=HTMLResponse)
    async def archive_inbox(request: Request):
        values = await form_values(request)
        inbox_id = values.get("inbox_id", "")
        mode = values.get("mode", "archive")
        if inbox_id:
            argv = ["LifeRPG.Inbox.Archive", "--inbox-id", inbox_id]
            if mode == "delete":
                argv.append("--delete")
            _skill(context, argv)
            return render(request, "partials/inbox_items.html", {"notice": "Inbox item removed.", "page": "inbox"})
        return render(request, "partials/inbox_items.html", {"notice": "Inbox item missing.", "page": "inbox"})

    @app.post("/inbox/revert", response_class=HTMLResponse)
    async def revert_inbox(request: Request):
        inbox_id = await form_value(request, "inbox_id")
        if inbox_id:
            _skill(context, ["LifeRPG.Inbox.Revert", "--inbox-id", inbox_id])
            return render(request, "partials/inbox_items.html", {"notice": "Inbox item reverted.", "page": "inbox"})
        return render(request, "partials/inbox_items.html", {"notice": "Inbox item missing.", "page": "inbox"})

    @app.post("/quest/create", response_class=HTMLResponse)
    async def create_quest(request: Request):
        values = await form_values(request)
        title = values.get("title", "")
        if title:
            argv = ["LifeRPG.Quest.Create", "--title", title]
            for field, flag in (
                ("category", "--category"),
                ("minimum_win", "--minimum-win"),
                ("priority", "--priority"),
                ("energy_cost", "--energy-cost"),
            ):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/quest_list.html", {"notice": "Quest created.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest title required.", "page": "quests"})

    @app.post("/quest/edit", response_class=HTMLResponse)
    async def edit_quest(request: Request):
        values = await form_values(request)
        quest_id = values.get("quest_id", "")
        if quest_id:
            argv = ["LifeRPG.Quest.Edit", "--quest-id", quest_id]
            for field, flag in (
                ("title", "--title"),
                ("category", "--category"),
                ("minimum_win", "--minimum-win"),
                ("priority", "--priority"),
                ("energy_cost", "--energy-cost"),
                ("status", "--status"),
            ):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/quest_list.html", {"notice": "Quest updated.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest missing.", "page": "quests"})

    @app.post("/quest/archive", response_class=HTMLResponse)
    async def archive_quest(request: Request):
        values = await form_values(request)
        quest_id = values.get("quest_id", "")
        mode = values.get("mode", "archive")
        if quest_id:
            argv = ["LifeRPG.Quest.Archive", "--quest-id", quest_id]
            if mode == "delete":
                argv.append("--delete")
            _skill(context, argv)
            return render(request, "partials/quest_list.html", {"notice": "Quest removed.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest missing.", "page": "quests"})

    @app.post("/quest/add-step", response_class=HTMLResponse)
    async def add_quest_step(request: Request):
        values = await form_values(request)
        quest_id = values.get("quest_id", "")
        title = values.get("title", "")
        if quest_id and title:
            _skill(context, ["LifeRPG.Quest.AddStep", "--quest-id", quest_id, "--title", title])
            return render(request, "partials/quest_list.html", {"notice": "Quest step added.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest step needs text.", "page": "quests"})

    @app.post("/quest/check-step", response_class=HTMLResponse)
    async def check_quest_step(request: Request):
        values = await form_values(request)
        quest_id = values.get("quest_id", "")
        step_id = values.get("step_id", "")
        if quest_id and step_id:
            _skill(context, ["LifeRPG.Quest.CheckStep", "--quest-id", quest_id, "--step-id", step_id])
            return render(request, "partials/quest_list.html", {"notice": "Quest step updated.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest step missing.", "page": "quests"})

    @app.post("/quest/add-note", response_class=HTMLResponse)
    async def add_quest_note(request: Request):
        values = await form_values(request)
        quest_id = values.get("quest_id", "")
        note = values.get("note", "")
        if quest_id and note:
            _skill(context, ["LifeRPG.Quest.AddNote", "--quest-id", quest_id, "--note", note])
            return render(request, "partials/quest_list.html", {"notice": "Quest note added.", "page": "quests"})
        return render(request, "partials/quest_list.html", {"notice": "Quest note needs text.", "page": "quests"})

    @app.post("/quest/start", response_class=HTMLResponse)
    async def start_quest(request: Request):
        inbox_id = await form_value(request, "inbox_id")
        quest_id = await form_value(request, "quest_id")
        if inbox_id:
            _skill(context, ["LifeRPG.Quest.Start", "--inbox-id", inbox_id])
        elif quest_id:
            _skill(context, ["LifeRPG.Quest.Start", "--quest-id", quest_id])
        return render_fragment(
            request,
            "partials/active_session.html",
            extra={"notice": "Quest session started."},
            oob_templates=[
                "partials/expedition.html",
                "partials/inbox_items.html",
                "partials/quest_list.html",
                "partials/roh_proposals.html",
            ],
        )

    @app.post("/quest/pause", response_class=HTMLResponse)
    async def pause_quest(request: Request):
        quest_id = await form_value(request, "quest_id")
        note = await form_value(request, "note")
        if quest_id:
            _skill(context, ["LifeRPG.Quest.Pause", "--quest-id", quest_id, "--note", clean_text(note)])
        return render_fragment(
            request,
            "partials/active_session.html",
            extra={"notice": "Quest session paused."},
            oob_templates=["partials/expedition.html", "partials/quest_list.html", "partials/roh_proposals.html"],
        )

    @app.post("/quest/complete", response_class=HTMLResponse)
    async def complete_quest(request: Request):
        quest_id = await form_value(request, "quest_id")
        note = await form_value(request, "note")
        if quest_id:
            _skill(context, ["LifeRPG.Quest.Complete", "--quest-id", quest_id, "--note", clean_text(note)])
        return render_fragment(
            request,
            "partials/active_session.html",
            extra={"notice": "Quest completed. Rewards resolved."},
            oob_templates=[
                "partials/expedition.html",
                "partials/reward_panel.html",
                "partials/quest_list.html",
                "partials/roh_proposals.html",
            ],
        )

    @app.post("/habit/create", response_class=HTMLResponse)
    async def create_habit(request: Request):
        values = await form_values(request)
        title = values.get("title", "")
        if title:
            argv = ["LifeRPG.Habit.Create", "--title", title]
            for field, flag in (("category", "--category"), ("cadence", "--cadence")):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/habit_list.html", {"notice": "Habit created.", "page": "today"})
        return render(request, "partials/habit_list.html", {"notice": "Habit title required.", "page": "today"})

    @app.post("/habit/edit", response_class=HTMLResponse)
    async def edit_habit(request: Request):
        values = await form_values(request)
        habit_id = values.get("habit_id", "")
        if habit_id:
            argv = ["LifeRPG.Habit.Edit", "--habit-id", habit_id]
            for field, flag in (("title", "--title"), ("category", "--category"), ("cadence", "--cadence")):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/habit_list.html", {"notice": "Habit updated.", "page": "today"})
        return render(request, "partials/habit_list.html", {"notice": "Habit missing.", "page": "today"})

    @app.post("/habit/archive", response_class=HTMLResponse)
    async def archive_habit(request: Request):
        values = await form_values(request)
        habit_id = values.get("habit_id", "")
        mode = values.get("mode", "archive")
        if habit_id:
            argv = ["LifeRPG.Habit.Archive", "--habit-id", habit_id]
            if mode == "delete":
                argv.append("--delete")
            _skill(context, argv)
            return render(request, "partials/habit_list.html", {"notice": "Habit removed.", "page": "today"})
        return render(request, "partials/habit_list.html", {"notice": "Habit missing.", "page": "today"})

    @app.post("/habit/check", response_class=HTMLResponse)
    async def check_habit(request: Request):
        habit_id = await form_value(request, "habit_id")
        if habit_id:
            _skill(context, ["LifeRPG.Habit.Check", "--habit-id", habit_id])
        return render(request, "partials/habit_list.html", {"notice": "Habit checked.", "page": "today"})

    @app.post("/event/create", response_class=HTMLResponse)
    async def create_event(request: Request):
        values = await form_values(request)
        title = values.get("title", "")
        starts_at = values.get("starts_at", "")
        if title and starts_at:
            argv = ["LifeRPG.Event.Create", "--title", title, "--starts-at", starts_at]
            for field, flag in (
                ("ends_at", "--ends-at"),
                ("reminder_minutes", "--reminder-minutes"),
                ("status", "--status"),
            ):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/event_list.html", {"notice": "Event created.", "page": "today"})
        return render(request, "partials/event_list.html", {"notice": "Event title and start are required.", "page": "today"})

    @app.post("/event/edit", response_class=HTMLResponse)
    async def edit_event(request: Request):
        values = await form_values(request)
        event_id = values.get("event_id", "")
        if event_id:
            argv = ["LifeRPG.Event.Edit", "--event-id", event_id]
            for field, flag in (
                ("title", "--title"),
                ("starts_at", "--starts-at"),
                ("ends_at", "--ends-at"),
                ("reminder_minutes", "--reminder-minutes"),
                ("status", "--status"),
            ):
                if values.get(field):
                    argv.extend([flag, values[field]])
            _skill(context, argv)
            return render(request, "partials/event_list.html", {"notice": "Event updated.", "page": "today"})
        return render(request, "partials/event_list.html", {"notice": "Event missing.", "page": "today"})

    @app.post("/event/archive", response_class=HTMLResponse)
    async def archive_event(request: Request):
        values = await form_values(request)
        event_id = values.get("event_id", "")
        mode = values.get("mode", "archive")
        if event_id:
            argv = ["LifeRPG.Event.Archive", "--event-id", event_id]
            if mode == "delete":
                argv.append("--delete")
            _skill(context, argv)
            return render(request, "partials/event_list.html", {"notice": "Event removed.", "page": "today"})
        return render(request, "partials/event_list.html", {"notice": "Event missing.", "page": "today"})

    @app.post("/settings/save", response_class=HTMLResponse)
    async def save_settings(request: Request):
        values = await form_values(request)
        argv = [
            "LifeRPG.Settings.Update",
            "--display-name",
            values.get("display_name", ""),
            "--timezone",
            values.get("timezone", ""),
            "--auto-sort-enabled",
            values.get("auto_sort_enabled", "false"),
            "--checkin-minutes",
            values.get("checkin_minutes", ""),
            "--reward-intensity",
            values.get("reward_intensity", ""),
            "--strictness-mode",
            values.get("strictness_mode", ""),
            "--visual-mode",
            values.get("visual_mode", ""),
        ]
        _skill(context, argv)
        return render(request, "partials/settings_panel.html", {"notice": "Settings saved."})

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
            "quests": "partials/quest_list.html",
            "settings": "partials/settings_panel.html",
        }
        template = allowed.get(name)
        if not template:
            return RedirectResponse("/")
        return render(request, template)

    return app
