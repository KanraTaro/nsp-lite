# NSPL.Status

`Web/NSPL/Status` is the reference NSPL Web app.

It proves the current Web path:

```text
Web app -> WebContext -> nspl.py -> Entry skill surface -> Skill
```

The app calls `NSPL.Tools.Time.now` through `WebContext` and displays the
captured skill result.

## Routes

- `/`: HTML status page
- `/health`: small JSON health response
- `/api/status`: JSON status payload including app metadata, repo root, time
  payload, and captured skill stdout/stderr/exit code

## Launch

From the repo root:

```bash
python -m pip install -e ".[web]"
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
```

The server runs in the foreground until stopped.
