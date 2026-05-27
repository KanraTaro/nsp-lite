# NSPL Entry

`Core/NSPL/Entry` is the canonical command spine for NSPL.

The root `nspl.py` script is the bootstrap gateway. It resolves the repo root
and caller cwd, validates the root, puts the repo on `sys.path`, exports
`NSPL_CALLER_CWD`, changes into the repo root for stable discovery, and then
delegates to Entry.

## Entry Context

Entry receives an `EntryContext` containing:

- `repo_root`
- `caller_cwd`

Surface commands use that context to resolve descriptor roots and preserve the
user's original cwd while running from a stable repo root.

## Surfaces

Entry currently routes:

```bash
python nspl.py skill ...
python nspl.py gui ...
python nspl.py web ...
```

### skill

The skill surface executes one skill per invocation:

```bash
python nspl.py skill list
python nspl.py skill NSPL.Tools.Time.now --json
```

Discovery uses `Skills/<Domain>/<SkillName>/skill.json`. Listing does not
import skill modules. Running a skill imports exactly one module and provides
the standard skill context, including `ctx.node_ctx` and `ctx.json`.

### gui

The gui surface lists and launches desktop/native shells:

```bash
python nspl.py gui list
python nspl.py gui run Video.LookLab
```

Discovery uses `GUI/<Domain>/<GuiName>/gui.json`. GUIs are shells over Core and
Skills, not separate execution engines.

### web

The web surface discovers, lists, and launches browser/mobile shells:

```bash
python nspl.py web list
python nspl.py web list --detailed
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
```

Discovery uses `Web/<Domain>/<AppName>/web.json`. Listing reads descriptors
only and does not import app modules.

Install optional Web dependencies with:

```bash
python -m pip install -e ".[web]"
```

## Web Launch Lifecycle

`python nspl.py web launch <Name>`:

1. discovers `web.json` descriptors under `Web/` or `WEB_ROOT`
2. resolves the named app
3. imports only that app's entry module
4. builds a `WebContext`
5. calls the configured factory, usually `create_app(context)`
6. starts Uvicorn as a foreground local server

Web apps must not start Uvicorn themselves. Entry owns host/port binding,
reload mode, log level, dependency errors, and foreground server lifecycle.

The default host is `127.0.0.1`, unless overridden by the descriptor or command
line. LAN or Tailscale access requires an explicit bind and external network
configuration.

## WebContext

`WebContext` gives Web apps:

- `repo_root`
- `caller_cwd`
- `web_root`
- `app_dir`
- descriptor `metadata`
- app `entry_path`
- `factory_name`

`WebContext.run_skill(argv, timeout=30.0)` invokes the skill surface through the
real repo `nspl.py` gateway in a subprocess. The `argv` shape is the skill
surface shape after `nspl.py skill`, for example:

```python
context.run_skill([
    "NSPL.Tools.Time.now",
    "--timezone",
    "America/New_York",
    "--json",
])
```

This keeps concurrent Web requests from mutating process-wide skill environment
state while preserving the same command path used by humans and automation.

## Compatibility Shims

`Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` remain supported compatibility
entrypoints. Their public command shapes are preserved for existing callers:

```bash
python -m Core.NSPL.SkillCLI list
python -m Core.NSPL.SkillCLI skill NSPL.Tools.Time.now --json
python -m Core.NSPL.GUICLI list
```

Do not add new command-surface behavior there. New surfaces and new routing
belong under Entry.
