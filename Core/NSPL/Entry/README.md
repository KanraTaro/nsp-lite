# NSPL Entry

`Core/NSPL/Entry` is the unified command spine behind the root `nspl.py`
gateway.

## One Entry, Many Surfaces

NSPL should expose one Entry with multiple surfaces:

- `skill` for one-shot action execution
- `gui` for desktop/native visual shells
- `web` for browser/mobile visual shells in a later pass

This pass only wires `skill` and `gui`.

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

## Later Passes

Web is intentionally not implemented here. A later pass should add the `web`
surface through Entry rather than creating a separate long-term CLI.
