# SkillCLI Compatibility Entrypoint

`Core/NSPL/SkillCLI` is the historical skill dispatcher package. It remains
supported for compatibility with existing scripts, tests, workers, and imports.

The canonical command spine is now `Core/NSPL/Entry`, reached through the root
`nspl.py` gateway:

```bash
python nspl.py skill list
python nspl.py skill skill NSPL.Tools.Time.now --json
```

The compatibility module path still works:

```bash
python -m Core.NSPL.SkillCLI list
python -m Core.NSPL.SkillCLI skill NSPL.Tools.Time.now --json
```

Do not add new command-surface behavior here. New routing and surfaces belong
under Entry.

## What This Package Preserves

- `skill.json` discovery under `Skills/`
- `SKILLS_ROOT` override behavior
- no-import-on-list discovery
- one-module-import-on-run execution
- standard skill context creation
- best-effort NodeCTX lifecycle logging
- existing public command grammar

## Skill Contract

Each skill directory contains:

```text
Skills/
  <Domain>/
    <SkillName>/
      skill.json
      skill.py
```

`skill.json`:

```json
{
  "name": "Example.Echo",
  "version": "0.1.0",
  "description": "Example skill"
}
```

`skill.py`:

```python
def build_parser(parser):
    ...


def run(args, ctx) -> int:
    ...
```

The context includes `ctx.root`, `ctx.node_tag`, `ctx.instance_id`,
`ctx.global_scope`, `ctx.node_ctx`, `ctx.debug`, and `ctx.json`.

Use `ctx.node_ctx` for durable state and logs. Skills should parse arguments,
perform one action, write clear stdout/stderr, and return an exit code.
