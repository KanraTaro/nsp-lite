# NSPL Protocols and Design Rules

## Purpose

This document defines the architectural laws that keep NSPL coherent.

These rules exist so humans, AI agents, Web apps, GUIs, Skills, local runtimes, and future multi-node systems can all work from the same durable assumptions.

If an implementation conflicts with this document, stop and ask unless the pass explicitly says the rule is being changed.

## Prime Directive

Filesystem state is authoritative.

If a system has durable state, progress, queues, active sessions, logs, reports, or user data, that state must be visible in files through the approved state layer.

Hidden memory, globals, browser-only state, process-local caches, and remote services may be used as temporary implementation details, but they must not become the durable source of truth unless explicitly approved.

## Layer Contract

### Core Owns Behavior

Core modules own reusable domain behavior.

Core should contain models, services, validation, policy, state access helpers, reusable algorithms, domain contracts, and testable behavior.

Core should not contain UI rendering, one-off CLI formatting, Web route templates, provider-specific UI assumptions, or hidden app server state.

### Skills Expose Actions

Skills are thin executable action surfaces.

A Skill should parse arguments, call Core, format stdout, respect `ctx.json`, return an exit code, and stay small.

A Skill should not own reusable business logic, call other Skills when Core should be shared, maintain hidden durable state, become a daemon, or invent direct state paths when NodeCTX/store helpers exist.

### Web Apps Are Control Surfaces

Web apps are user-facing browser/mobile shells.

They should guide the user, call Skills or approved Core seams, render state clearly, use HTMX/JS/CSS for interaction, keep durable truth in NodeCTX-backed files, update affected panels coherently, and remain local-first by default.

They should not become business logic centers, hide durable truth in browser state, expose unsafe raw tools, show raw CRUD walls as primary UX, or start their own Uvicorn server outside Entry.

### GUI Apps Are Control Surfaces

GUI apps are native/desktop visual shells. They may call Core directly where practical, but long-term they should align with Skills/Core behavior so GUI and Web surfaces do not diverge.

### Entry Is Canonical

`nspl.py` and `Core/NSPL/Entry` define the canonical command surface.

Current canonical surfaces:

- `skill`
- `web`
- `gui`

Flattened Skill syntax is canonical:

```bash
python nspl.py skill <Skill.Name> [args...]
```

Do not promote old doubled syntax:

```bash
python nspl.py skill <leading-skill-token> <Skill.Name>
```

External shell wrappers are local conveniences, not architecture.

## NodeCTX State Contract

Durable state must use the canonical NodeCTX layout:

```text
State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/
```

### InstanceId

The runtime instance. For MVP apps, this is often `main`. Future uses include separate user instances, separate app deployments, dev/prod instances, and hosted deployments.

### Scope

The state scope. Common values are `Global` or a node tag such as `Workstation`.

Use `Global` when the state should be shared across nodes for one user/instance. Use node tags when state belongs to a specific machine.

Future node targeting and conflict handling are not fully implemented yet. Do not fake them.

### Domain

The system or app domain, such as `LifeRPG`, `RohTalk`, `ChatOps`, `AutoRoh`, `DST`, or `Video`.

### Bucket

The state category. Common buckets are `Config`, `Data`, `Workflow`, `Logs`, and `Reflections`.

### Subpath

Domain-owned structure inside the bucket.

Examples:

```text
Data/Quests/<quest_id>.json
Workflow/Sessions/active/<session_id>.json
Logs/liferpg.events.jsonl
```

## Bucket Semantics

### Config

Configuration and profile preferences: app settings, user display name, default behavior toggles, profile-level preferences, and visual mode.

### Data

Canonical durable objects: quests, inbox items, habits, events, agents, conversations, provider records.

Data objects should generally persist independent of current workflow state.

### Workflow

Runtime operational state: active sessions, queues, proposals, pending rewards, current mission, active expedition, task claim folders, temporary action state.

### Logs

Append-only or audit-style records: event logs, action logs, Roh action logs, tool call results, lifecycle traces.

Logs should support replay, debugging, and agent review.

### Reflections

Longer-form summaries and interpreted artifacts: daily reflections, session summaries, agent review notes, post-run analysis, generated reports.

## FPP Alignment

NSPL follows the Filesystem Pulse Protocol idea:

- active state should leave visible traces
- loops should write heartbeat/status files
- actions should log outcomes
- queues should be observable
- failures should be inspectable
- GUIs and Web apps should be able to render state by reading files or approved Core services

This makes systems easier to debug, sync, replay, and explain.

## Public vs Private State

Do not assume every state file is safe to share.

State may include personal tasks, logs, conversations, app settings, family information, local paths, provider IDs, and future credentials or tokens if not handled carefully.

Repo context zips should usually exclude:

```text
State/
.git/
__pycache__/
.pytest_cache/
*.egg-info/
*.pyc
.venv/
node_modules/
```

Public examples should use seeded/demo state, not personal runtime state.

## Skill Safety

Skills are powerful.

Model-facing toolkits should expose safe, semantic tools, not raw low-level command writers, unless explicitly approved.

Safe tool design:

- validate inputs
- use allowlists
- return structured results
- log actions
- avoid silent side effects
- avoid exposing unrestricted shell/file/network operations to models

## Web Safety

NSPL Web apps are currently local/development oriented.

Local-first safe default:

```bash
--host 127.0.0.1
```

Binding to LAN or server addresses can expose tools.

Public/server hosting needs authentication, user/profile isolation, skill permission allowlists, CSRF protection, deployment config, reverse proxy/HTTPS docs, audit logs, backup/restore, and public/private app boundaries.

Do not expose full NSPL command surfaces publicly yet.

## Agent Development Artifacts

Agent-assisted development must leave artifacts.

Important artifacts include design docs, implementation reports, tests, screenshots/mockups, status docs, known issues, context bundles, generated logs when appropriate, and commit messages.

Every significant agent pass should report:

- files changed
- goal
- behavior changed
- state/data changed
- tests run
- manual smoke
- deferred work
- risks
- next suggested pass

Reports should be saved under `Docs/Reports/` when useful.

## UX Rules Are Architecture Rules

For NSPL Web apps, UX is not decoration. A bad UI can make a correct system unusable.

Minimum rules:

- dashboards guide, management pages manage
- no raw CRUD walls as default screens
- use progressive disclosure
- use selects for enum-like fields
- settings must do something visible or be clearly marked future/deferred
- state-changing actions should update all affected panels
- mobile matters
- visual feedback matters

## Testing Rules

Tests are part of the architecture.

Add or update tests when changing Core behavior, Skill behavior, Web routes, NodeCTX paths, command syntax, app state schema, UX contracts that can be asserted, bundle generation, or integration seams.

Typical validation:

```bash
python -m py_compile <changed files>
python -m unittest <focused test module>
python run_tests.py
python nspl.py skill list
python nspl.py web list
git diff --check
```

Manual smoke is still required for Web/GUI UX.

## Dependency Rules

Base/Core should stay as stdlib-first as practical.

Optional surfaces may require extras:

- Web may require FastAPI/Uvicorn/Jinja2/HTMX assets
- GUI may require PySide/PyQt
- Video may require FFmpeg
- LLM features may require Ollama or model backends

Dependencies should be declared or documented. Import optional dependencies only in paths that need them when practical.

## Hardcoding Rules

Do not hardcode user-specific behavior in public Core logic.

Allowed:

- tests using sample names
- local profile/config defaults
- project-specific docs
- private State files

Not allowed:

- Core assumptions that every user is a specific person
- fixed local paths in reusable logic
- user-specific categories as global rules
- personal state in source docs or tests

## Multi-Node Rules

NSPL is intended to grow into multi-node systems, but do not pretend unfinished features exist.

Current safe assumption:

- Global scope works for MVP local shared state.
- Separate users can use separate instances/ports for now.
- Node targeting and conflict strategy are deferred platform features.

Future multi-node work needs node identity, target-node routing, state freshness checks, conflict markers, merge/recovery strategies, permissions, and audit trails.

## Design Change Rule

When changing architecture, document why the change is needed, what contract changes, what files are affected, what tests prove it, what old behavior remains compatible, and what migration is needed.

Do not silently drift architecture because it was convenient in one pass.

## Summary

The NSPL design rule in one sentence:

> Put durable truth in files, reusable behavior in Core, executable actions in Skills, user control in Web/GUI surfaces, and development context in artifacts that both humans and AI agents can follow.
