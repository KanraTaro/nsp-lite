import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def _parse_time_payload(result) -> tuple[Dict[str, Any] | None, str | None]:
    if result.exit_code != 0:
        return None, "time skill returned a non-zero exit code"

    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"could not parse time skill JSON: {exc}"


def _load_status_payload(context) -> Dict[str, Any]:
    result = context.run_skill_subprocess(
        [
            "NSPL.Tools.Time.now",
            "--timezone",
            "America/New_York",
            "--json",
        ]
    )
    payload, parse_error = _parse_time_payload(result)

    return {
        "app": context.metadata.get("name", "NSPL.Status"),
        "version": context.metadata.get("version", ""),
        "repo_root": str(context.repo_root),
        "time": payload or {},
        "parse_error": parse_error,
        "skill": result.as_dict(),
    }


def create_app(context):
    app_dir = Path(context.app_dir)
    templates = Jinja2Templates(directory=str(app_dir / "templates"))

    app = FastAPI(title="NSPL Status")
    app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")

    @app.get("/health")
    async def health():
        return {"ok": True, "app": context.metadata.get("name", "NSPL.Status")}

    @app.get("/api/status", response_class=JSONResponse)
    async def api_status():
        return _load_status_payload(context)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        status = _load_status_payload(context)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "repo_root": status["repo_root"],
                "app_name": status["app"],
                "app_version": status["version"],
                "time_payload": status["time"],
                "parse_error": status["parse_error"],
                "skill_result": status["skill"],
            },
        )

    return app
