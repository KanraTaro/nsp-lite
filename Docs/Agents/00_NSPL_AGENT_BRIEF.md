# NSPL Agent Brief

## Purpose

This document is the first-context packet for any AI agent working in the NSPLDev repository.

NSPL is a local-first, filesystem-backed application/runtime architecture. It is designed so Core logic, Skills, Web apps, GUIs, automation loops, and RohTalk tooling can all share the same durable state and command surfaces without hiding important behavior inside opaque services.

The short version:

- Filesystem state is authoritative.
- Core owns reusable behavior.
- Skills expose thin executable actions.
- Web and GUI apps are control surfaces.
- Entry is the canonical command gateway.
- NodeCTX owns durable state routing.
- Tests and README updates are part of the work, not optional polish.

## Always Read First

Agents should read these before modifying code:

1. `AGENTS.md`
2. `00_AGENT_HANDOFF.md`
3. `Docs/Agents/00_NSPL_AGENT_BRIEF.md`
4. `Docs/Agents/01_NSPL_ARCHITECTURE_AND_COMMANDS.md`
5. `Docs/Agents/02_PROJECT_CONTEXTS.md`
6. `Docs/Agents/03_AGENT_WORKFLOW_AND_STATUS.md`
7. Any project-specific design doc under `Docs/Plans/`
8. Relevant README files in touched folders

If the handoff conflicts with repo rules, stop and ask unless the handoff explicitly says it supersedes a rule.

## Non-Negotiable Architecture Rules

- Do not bypass NodeCTX for durable state.
- Do not add databases, brokers, hidden daemons, or external services unless explicitly requested.
- Do not move business logic into Web routes or GUI launchers.
- Do not put reusable behavior in Skill wrappers.
- Do not expose raw low-level command tools to model-facing toolkits unless explicitly requested.
- Do not change public skill names unless the pass explicitly allows migration.
- Do not use old doubled skill syntax.
- Do not touch unrelated domains as drive-by cleanup.
- Do not commit generated logs, runtime State, pycache, egg-info, or scan dumps.

## Layer Responsibilities

### Core

`Core/<Domain>/...` owns reusable logic, contracts, validation, state services, policy, and model-independent behavior.

Core should be boring, testable, and UI-free.

### Skills

`Skills/<Domain>/<Skill>/...` exposes thin CLI/agent actions that call Core.

Skills should parse args, call Core, format output, and return an exit code. They should not own reusable policy.

### Web

`Web/<Domain>/<App>/...` exposes browser/mobile control surfaces.

Web apps launch through Entry, expose `create_app(context)`, and should not start Uvicorn directly. Web should orchestrate UI and call Skills/Core through approved seams, not become the source of truth.

### GUI

`GUI/<Domain>/<Gui>/...` exposes desktop/native visual shells. Current GUI examples may call Core directly, but the long-term target is thinner shells aligned with Skill behavior where practical.

### State

`State/` is runtime data. It is not source. It should normally be excluded from repo zips and commits.

## Current Important Domains

- `Core/NSPL`: platform spine, Entry, NodeCTX, SkillCLI, WebContext, ProjectRoot, Proc, Deps, ChatOps.
- `Core/RohTalk`: persistent tool-capable conversation runtime.
- `Core/LifeRPG`: gamified life command center logic.
- `Core/Game/DST`: Don't Starve Together RohBridge contracts and command transport.
- `Core/AutoRoh`: generic observed tool-capable worker loop.
- `Core/Video`: reusable FFmpeg/video/frame processing logic.
- `GUI/Video/LookLab`: first usable GUI vertical slice.
- `Web/LifeRPG/App`: first major browser/mobile app.
- `Web/NSPL/Status`: reference Web app proving Entry/Web/Skill loop.

## Current Product Direction

NSPL is being shaped into a local-first system where Roh can use persistent conversations, tools, Web apps, game bridges, media tools, and filesystem state to act as a real operator instead of a stateless chatbot.

LifeRPG and RohTalk are strategic centerpieces:

- RohTalk makes Roh persistent, tool-capable, and app-usable.
- LifeRPG turns day management into missions, quests, habits, events, rewards, and an idle expedition loop.

DST/RohBridge is the game-action proof path. Video/LookLab is the creator-tooling proof path.

## Agent Behavior Standard

Agents should behave like careful implementers, not product owners.

For coding passes:

- Make small, testable, reversible changes.
- Explain exact files changed.
- Run focused tests.
- Run `python run_tests.py` when behavior changes and practical.
- Update README/docs when behavior or command surfaces change.
- Report uncertainty honestly.

For review passes:

- Do not edit files unless explicitly asked.
- Compare implementation against design contracts.
- Call out architecture drift and UX/product failures clearly.

## Common Failure Modes to Avoid

- Passing tests while producing unusable UX.
- Adding raw CRUD forms everywhere instead of progressive disclosure.
- Using free-text inputs for enum-like fields.
- Making Web routes the owner of business logic.
- Forgetting cross-panel updates in HTMX apps.
- Creating app settings that do not affect anything.
- Hardcoding user-specific behavior in Core.
- Letting model-facing tools call unsafe raw command writers.
