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

## Current Delegation

For compatibility, Entry currently delegates:

- `skill` to `Core.NSPL.SkillCLI.skillcli.main`
- `gui` to `Core.NSPL.GUICLI.guicli.main`

That preserves the existing `skill.json` and `gui.json` contracts, existing
environment overrides, no-import-on-list behavior, one-module-import-on-run
behavior, and existing best-effort NodeCTX logging.

## Later Passes

Web is intentionally not implemented here. A later pass should add the `web`
surface through Entry rather than creating a separate long-term CLI.
