import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def _parse_time_payload(result) -> tuple[Dict[str, Any] | None, str | None]:
    if result.exit_code != 0:
        return None, "time skill returned a non-zero exit code"

    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"could not parse time skill JSON: {exc}"


def create_app(context):
    app_dir = Path(context.app_dir)
    templates = Jinja2Templates(directory=str(app_dir / "templates"))

    app = FastAPI(title="NSPL Status")
    app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        result = context.run_skill(
            [
                "skill",
                "NSPL.Tools.Time.now",
                "--timezone",
                "America/New_York",
                "--json",
            ]
        )
        payload, parse_error = _parse_time_payload(result)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "repo_root": str(context.repo_root),
                "app_name": context.metadata.get("name", "NSPL.Status"),
                "app_version": context.metadata.get("version", ""),
                "time_payload": payload or {},
                "parse_error": parse_error,
                "skill_result": result.as_dict(),
            },
        )

    return app
