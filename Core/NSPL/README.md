# NSPL Core

`Core/NSPL` contains the framework primitives that define NSP Lite: Entry,
filesystem context, durable logging, compatibility command packages, and root
discovery.

Nothing in this directory is a skill. Core modules own reusable logic,
contracts, validation, and policy.

## Canonical Entry

`Core/NSPL/Entry` is the canonical command spine behind the root `nspl.py`
gateway.

`nspl.py` performs bootstrap work only:

- resolve and validate the repo root
- preserve caller cwd context
- put the repo root on `sys.path`
- export `NSPL_CALLER_CWD`
- run Entry from the repo root

After bootstrap, Entry routes command surfaces:

- `skill`: one-shot action execution
- `gui`: desktop/native shells
- `web`: browser/mobile shells

## Surfaces

Skills are one-shot action surfaces. They parse arguments, call Core, use
NodeCTX for durable filesystem work, print clear output, and exit.

GUI and Web are shells/control surfaces. They can observe state and invoke
skills, but reusable behavior still belongs in Core or Skills.

Web discovery, listing, and launch now live under Entry. Web apps live under
`Web/<Domain>/<AppName>/`, use `web.json`, expose `create_app(context)`, and do
not start Uvicorn themselves.

## Compatibility Packages

`Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` remain importable and executable for
compatibility with existing commands, tests, scripts, and local wrappers. They
are no longer the architecture center. New command-surface behavior should live
under Entry.

Do not add new behavior to SkillCLI/GUICLI unless it is required to preserve or
repair compatibility.

## Filesystem Truth

NSPL is filesystem-truth first.

If something must be durable across crashes, inspectable by humans/tools,
replayable for debugging, or syncable between machines, it must exist as a file
artifact, typically under `State/`.

There is no hidden database, broker, daemon, cloud queue, or private in-memory
service that acts as the source of truth.

Databases may be added only as derived projections or caches that can be rebuilt
from file artifacts. They must never be the only copy of important state.

## Modules

### Entry

Canonical command routing for `skill`, `gui`, and `web` surfaces.

### NodeCTX

Filesystem and logging utilities:

- canonical state and log paths
- atomic JSON writes
- durable JSONL append
- best-effort event logging

### SkillCLI

Compatibility entrypoint for the skill surface. The public command shape and
skill contract remain supported.

### GUICLI

Compatibility entrypoint for the GUI surface. Existing `gui.json` discovery and
launch behavior remain supported.

### ProjectRoot

Runtime root discovery utilities used by tests, tools, and compatibility paths.

## Portability Contract

Core/base remains stdlib-first. Optional Web dependencies are declared behind
the `web` extra and are imported only on Web launch paths.

Core/NSPL should remain usable on Linux, macOS, Windows, and headless systems.
No background service is required to understand system state.

External tools are optional integrations. Their absence should be detected
explicitly and reported clearly.
