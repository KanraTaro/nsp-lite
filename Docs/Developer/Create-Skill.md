# Create A Skill

Skills are one-shot action entrypoints under `Skills/<Domain>/<SkillName>/`.

They are invoked through the Entry skill surface. The historical
`Core.NSPL.SkillCLI` module path remains available for compatibility.

## Minimal Structure

```text
Skills/
  Example/
    Echo/
      skill.json
      skill.py
```

Nested skill directories are also allowed when a domain needs deeper grouping.

## skill.json

```json
{
  "name": "Example.Echo",
  "version": "0.1.0",
  "description": "Print a message"
}
```

## skill.py

```python
import argparse
import json


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("message")


def run(args, ctx) -> int:
    payload = {"message": args.message}

    if ctx.json:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(args.message)

    return 0
```

`build_parser(parser)` adds skill-specific arguments. `run(args, ctx)` performs
one action and returns an integer exit code.

Use `ctx.node_ctx` for durable filesystem work. Do not make raw filesystem
writes for state or logs when NodeCTX provides the needed operation.

## List And Run

```bash
python nspl.py skill list
python nspl.py skill skill Example.Echo -- hello
python nspl.py skill skill Example.Echo --json -- hello
```

The `--json` flag is a skill-surface flag exposed as `ctx.json`. Skills should
emit machine-readable stdout when it is set.

## Common Mistakes

- Putting lifecycle loops, daemons, or schedulers inside a skill.
- Storing hidden durable state in globals, temp files, or private caches.
- Skipping clear stdout, stderr, and exit-code behavior.
- Importing other skills instead of moving reusable logic into Core.
- Doing sys.path, root discovery, or runtime bootstrap inside `skill.py`.
