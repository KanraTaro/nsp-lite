# **SkillCLI - RohTalk Skill Dispatcher (v1)**

SkillCLI is the standard command-line dispatcher for RohTalk skills.

It provides a **stable execution spine** for action-oriented skills by solving two core problems:

1. **Consistency**
   Every skill is invoked with the same argument structure, standard flags, error handling, and a shared runtime context (project root, node identity, durable I/O helpers).

2. **Lazy dispatch**
   Skills are discovered via metadata (`skill.json`) without importing their Python modules at startup.
   Only the selected skill is imported and executed.

SkillCLI is intentionally small, explicit, and predictable.
It is infrastructure - **not** an application layer.

---

## Design stance (important)

**Skills are executed exclusively via SkillCLI.**

Direct execution of `skill.py` files is **out of scope** for v1 and not guaranteed to work.

This constraint is intentional and enables:

* Zero bootstrap code inside skills
* No `sys.path` manipulation in skill modules
* A single, authoritative source of runtime context

If a user needs a GUI, worker process, or double-click entry point, it should invoke SkillCLI internally.

---

## Package layout

```
Core/
  SkillCLI/        # dispatcher, loader, context helpers
  NodeCTX/         # durable write helpers and path routing
  ProjectRoot/     # runtime root discovery utilities

Skills/
  <Domain>/
    <SkillName>/
      skill.json   # discovery metadata (no imports)
      skill.py     # executable implementation
```

`Core/SkillCLI` is **not a skill**.
It is framework infrastructure that skills depend on indirectly via the context object.

---

## Invocation

SkillCLI is invoked as a Python module:

```sh
python -m Core.NSPL.SkillCLI <command>
```

This ensures the repository root is bootstrapped correctly and all `Core.*` imports resolve consistently.

---

## Commands

### List available skills

```sh
python -m Core.NSPL.SkillCLI list [--detailed]
```

* Recursively scans `Skills/` for `skill.json`
* **Does not import** any `skill.py` modules
* Prints one skill name per line

Example:

```
Dummy.echo
ImportError.explode
```

With `--detailed`:

```
Dummy.echo	0.1.0	Echo a message back to the user
ImportError.explode	0.0.1	A skill designed to explode on import for testing
```

---

### Run a skill

```sh
python -m Core.NSPL.SkillCLI skill <SkillName> [skill arguments...]
```

Execution flow:

1. Resolve the skill via `skill.json`
2. Import **exactly one** module (`skill.py`)
3. Build an argument parser:

   * Standard flags (provided by SkillCLI)
   * Skill-specific arguments (`build_parser`)
4. Construct a runtime context object
5. Call `run(args, ctx)`
6. Exit with the returned status code

---

## Skill contract (v1)

Each skill **must** define:

### `skill.json`

Minimum required fields:

```json
{
  "name": "ChatOps.send_task",
  "version": "0.1.0",
  "description": "Submit a ChatOps task into the queue"
}
```

Optional:

* `"entry"` - defaults to `"skill.py"`

The `name` must be globally unique across all skills.

---

### `skill.py`

Each skill module must export **exactly two callables**:

#### `build_parser(parser: argparse.ArgumentParser) -> None`

* Extend the provided parser with skill-specific arguments
* **Do not** call `parse_args()`

#### `run(args: argparse.Namespace, ctx: SkillContext) -> int`

* Execute the skill
* Return an integer exit code (`0` = success)
* All filesystem interaction **must go through `ctx.node_ctx`**

Optional:

* `SKILL_META` dictionary (for introspection only; not used for discovery)

---

## Canonical skill template

This is the **recommended starting point** for all new skills:

```python
# Skills/<Domain>/<SkillName>/skill.py

import argparse

def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("message", help="Message to print")

def run(args: argparse.Namespace, ctx) -> int:
    print(args.message)
    return 0
```

Key rules:

* **Do not import** `NodeCTX`, `ProjectRoot`, or `SkillCLI`
* **Do not** modify `sys.path`
* Treat `ctx` as the sole runtime interface

---

## Context object

When a skill is executed, SkillCLI constructs a `SkillContext` and passes it to `run()`.

The context exposes:

* `root`
  `pathlib.Path` pointing to the repository root

* `node_tag`
  Current node identifier (overridable via `--node`)

* `instance_id`
  Current instance identifier (overridable via `--instance`)

* `global_scope`
  Boolean flag from `--global`

* `node_ctx`
  Reference to the `Core.NSPL.NodeCTX` module
  **All durable writes and canonical paths must go through this**

* `debug`
  Whether `--debug` was supplied

* `json`
  Whether `--json` was supplied

Skills should treat the context as a **stable API surface**, not an implementation detail.

---

## Standard flags (available to all skills)

SkillCLI automatically adds the following flags to every skill:

* `--debug`
  Print full tracebacks on uncaught exceptions

* `--json`
  Request JSON-formatted output (skill-specific)

* `--node <tag>`
  Override node identifier

* `--instance <id>`
  Override instance identifier

* `--global`
  Operate in global scope instead of node scope

Skill-specific arguments are added on top of these via `build_parser()`.

---

## Skill discovery root override

By default, skills are discovered under:

```
<repo>/Skills/
```

For testing or advanced usage, discovery can be overridden via:

```sh
export SKILLS_ROOT=path/to/skills
```

Relative paths are resolved relative to the project root.

This mechanism exists primarily for unit tests.

---

## Error handling

SkillCLI provides structured, human-readable errors:

* Missing skills
* Duplicate skill names
* Invalid `skill.json`
* Import or execution failures

Behavior:

* Errors produce a non-zero exit code
* With `--debug`, full tracebacks are printed
* Without `--debug`, errors are concise and user-facing

---

## Non-goals for v1

The following are **explicitly out of scope**:

* Direct execution of `skill.py`
* ChatOps orchestration or session management
* GUI concerns
* Long-running workers or daemons
* Packaging, freezing, or installers
* Writing state from the dispatcher itself
* Importing all skills at startup

SkillCLI exists solely to **locate, list, and invoke skills reliably**.

Higher-level systems (ChatOps, workers, GUIs) should build on top of it - not inside it.
