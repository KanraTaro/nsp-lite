# SkillCLI – NSP Skill Dispatcher

SkillCLI is the standard command-line dispatcher for NSP skills.

It provides a stable execution spine for action-oriented systems by solving two core problems:

1. Consistency  
   Every skill is invoked with the same argument structure, flags, error handling, and runtime context.

2. Lazy dispatch  
   Skills are discovered via metadata (skill.json) and only imported when executed.

SkillCLI is infrastructure — not an application layer.

---

## Design stance (important)

Skills are executed exclusively via SkillCLI.

Direct execution of skill.py is not supported.

This enables:

- zero bootstrap code inside skills
- no sys.path hacks
- a single runtime context contract
- centralized logging and lifecycle
- consistent behavior across CLI, GUI, and workers

If something needs to run a skill, it should call SkillCLI.

---

## Relationship to NodeCTX

SkillCLI provides execution.

NodeCTX provides filesystem access.

Together:

- SkillCLI defines how code runs
- NodeCTX defines how code touches disk

### Rule of thumb

If your skill is interacting with:

- state
- config
- logs
- workflow files
- queues

you should be using:

ctx.node_ctx

not raw:

Path(...)
open(...)
os.replace(...)

NodeCTX is the filesystem boundary.

---

## Package layout

Core/
  NSPL/
    SkillCLI/
    NodeCTX/
    ProjectRoot/

Skills/
  <Domain>/
    <SkillName>/
      skill.json
      skill.py

SkillCLI is not a skill.  
It is runtime infrastructure.

---

## Invocation

python -m Core.NSPL.SkillCLI <command>

---

## Commands

### List skills

python -m Core.NSPL.SkillCLI list [--detailed]

- scans Skills/
- does not import skill modules
- prints names or metadata

---

### Run a skill

python -m Core.NSPL.SkillCLI skill <SkillName> [args...]

Execution flow:

1. resolve skill via skill.json
2. import exactly one module
3. build parser
4. construct context
5. log skill_started
6. run skill
7. log skill_finished or skill_failed
8. exit with code

---

## Dispatcher logging

SkillCLI automatically logs all executions via NodeCTX.

### Events

- skill_started
- skill_finished
- skill_failed

### Location

State/<Instance>/<Node|Global>/SkillCLI/Logs/skillcli.jsonl

### Guarantees

- best-effort only
- never blocks execution
- never alters exit codes

---

## Skill contract

Each skill must define:

### skill.json

{
  "name": "Example.echo",
  "version": "0.1.0",
  "description": "Example skill"
}

---

### skill.py

def build_parser(parser):
    ...

def run(args, ctx) -> int:
    ...

---

## The context object

SkillCLI provides a ctx object.

### Fields

- ctx.root
- ctx.node_tag
- ctx.instance_id
- ctx.global_scope
- ctx.node_ctx
- ctx.debug
- ctx.json

### Important

ctx.node_ctx is your filesystem interface.

---

## NodeCTX usage inside skills

This is the most important section.

### Pattern: build → read/write

def run(args, ctx):
    node_ctx = ctx.node_ctx

    path = node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        global_scope=ctx.global_scope,
        domain="Example",
        bucket="Data",
        subpath="items"
    )

    file_path = path / "item.json"

    node_ctx.write_json_atomic(file_path, {"value": 123})

    return 0

---

### Pattern: append logs

node_ctx.append_jsonl(log_path, {"event": "something"})

or use:

node_ctx.log_event(...)

---

### Pattern: list files

files = node_ctx.list_files(path, suffix=".json")

---

### Pattern: read data

data = node_ctx.read_json(file_path)
text = node_ctx.read_text(file_path)
lines = node_ctx.read_jsonl(log_path)

---

### Pattern: safe mutation

node_ctx.atomic_move_to_dir(src, dst_dir)
node_ctx.delete_file(path)

---

## What NOT to do

Avoid this in skills:

open(...)
Path(...).exists()
os.replace(...)

Unless you have a very specific reason.

If you need something NodeCTX doesn’t provide, extend NodeCTX instead.

---

## Canonical skill template

import argparse

def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("message")

def run(args, ctx) -> int:
    node_ctx = ctx.node_ctx

    print(args.message)
    return 0

---

## Standard flags

- --debug
- --json
- --node
- --instance
- --global

---

## Error handling

- return non-zero on failure
- structured errors preferred
- full traceback only with --debug
- logging still happens on failure

---

## Design rules

- skills do not manage runtime
- skills do not discover roots
- skills do not manage sys.path
- skills use NodeCTX for filesystem work

---

## Non-goals

- direct skill execution
- GUI logic
- workers
- orchestration
- packaging

SkillCLI exists to:

locate → invoke → observe → exit
