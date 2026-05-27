# Create A Web App

Web apps live under `Web/<Domain>/<AppName>/` and are launched by Entry.

## Minimal Structure

```text
Web/
  Example/
    Status/
      web.json
      app.py
      templates/    optional
      static/       optional
```

## Minimal web.json

```json
{
  "name": "Example.Status",
  "version": "0.1.0",
  "description": "Example status app",
  "entry": "app.py",
  "factory": "create_app",
  "default_host": "127.0.0.1",
  "default_port": 8765
}
```

## Minimal app.py

```python
from fastapi import FastAPI


def create_app(context):
    app = FastAPI(title=context.metadata.get("name", "Example.Status"))

    @app.get("/health")
    async def health():
        return {"ok": True, "app": context.metadata.get("name")}

    return app
```

Use `context.run_skill([...])` when the app needs behavior exposed by a skill:

```python
result = context.run_skill(["NSPL.Tools.Time.now", "--json"])
```

## List And Launch

```bash
python nspl.py web list
python nspl.py web launch Example.Status --host 127.0.0.1 --port 8765
```

Install optional dependencies when needed:

```bash
python -m pip install -e ".[web]"
```

## Common Mistakes

- Importing heavy optional dependencies during `web list`. Listing reads
  `web.json` only; keep heavy imports inside `app.py` launch paths.
- Starting Uvicorn inside `app.py`. Entry owns foreground server startup.
- Storing durable truth in browser storage, session memory, or process globals.
- Duplicating Skill/Core business logic inside the Web app.
- Binding to `0.0.0.0` without understanding local firewall and Tailscale/LAN
  exposure.
