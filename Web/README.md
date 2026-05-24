# Web Apps

`Web/` contains browser/mobile shells discovered and launched by the Entry web
surface.

Web apps are control surfaces over Core, NodeCTX, and Skills. They should not
own business logic, hidden durable state, or private workflow engines.

## Layout

```text
Web/
  <Domain>/
    <AppName>/
      web.json
      app.py
      templates/    optional
      static/       optional
```

## Descriptor

Each app has a `web.json` descriptor:

```json
{
  "name": "NSPL.Status",
  "version": "0.1.0",
  "description": "Local NSPL status Web app",
  "entry": "app.py",
  "factory": "create_app",
  "default_host": "127.0.0.1",
  "default_port": 8765
}
```

Fields:

- `name`: canonical app name, usually `<Domain>.<AppName>`
- `version`: app version string
- `description`: short listing text
- `entry`: Python module file relative to the app directory
- `factory`: callable in the entry module
- `default_host`: optional launch host
- `default_port`: optional launch port

`name`, `version`, and `description` are required for discovery. `entry`
defaults to `app.py`; `factory` defaults to `create_app`.

## App Contract

The entry module must expose:

```python
def create_app(context):
    ...
    return app
```

The returned object must be an ASGI app, typically a FastAPI app.

Web apps must not call `uvicorn.run()` or start their own server. Entry
`web launch` owns foreground server startup.

## Commands

List apps without importing them:

```bash
python nspl.py web list
python nspl.py web list --detailed
```

Launch an app:

```bash
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
```

Install optional Web dependencies first when needed:

```bash
python -m pip install -e ".[web]"
```
