# NSPL Entry

`Core/NSPL/Entry` is the unified command spine behind the root `nspl.py`
gateway.

## One Entry, Many Surfaces

NSPL should expose one Entry with multiple surfaces:

- `skill` for one-shot action execution
- `gui` for desktop/native visual shells
- `web` for browser/mobile visual shells

The `web` surface supports descriptor discovery, listing, and explicit
foreground local launch.

## nspl.py

The root `nspl.py` remains the bootstrapper. It owns repo-root resolution,
`--root`, `--cwd`, sys.path setup, caller cwd validation, `NSPL_CALLER_CWD`,
and running dispatch from the repo root.

After bootstrap, command routing belongs to Entry.

## Surface Implementations

Entry owns the shared surface implementations:

- `Core.NSPL.Entry.Surfaces.skill_surface`
- `Core.NSPL.Entry.Surfaces.gui_surface`

The historical `Core.NSPL.SkillCLI.skillcli` and `Core.NSPL.GUICLI.guicli`
modules are compatibility entrypoints over those Entry-owned implementations.
That preserves the existing `skill.json` and `gui.json` contracts, existing
environment overrides, no-import-on-list behavior, one-module-import-on-run
behavior, and existing best-effort NodeCTX logging while moving behavior under
Entry.

## Web Discovery

Web apps are discovered from:

`Web/<Domain>/<AppName>/web.json`

Supported commands:

- `python nspl.py web list`
- `python nspl.py web list --detailed`
- `python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765`

`WEB_ROOT` may override the default repo-local `Web/` root for tests and
advanced local setups. Listing reads descriptors only; it does not import
`app.py`.

Install optional Web dependencies with:

`python -m pip install -e ".[web]"`

Web launch is explicit and foreground. The default bind host is localhost.
Use `--host 0.0.0.0` or a LAN/Tailscale-reachable address only when you want
external devices to connect and have configured firewall/network access outside
NSPL.

## Later Passes

Future passes can add richer apps, but Web apps should remain shells over Core,
NodeCTX, and Skills.
