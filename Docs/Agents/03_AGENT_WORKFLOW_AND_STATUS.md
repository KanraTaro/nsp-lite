# Agent Workflow and Current Status

## Agent Roles

### Human Product Owner

- owns product judgment
- manual tests the app
- decides commits through GitKraken/git
- validates whether UX feels right
- provides external constraints and priorities

### ChatGPT / Roh in planning conversation

- thinking partner and design director
- prompt writer for Codex/Claude
- architecture reviewer
- converts messy requirements into scoped passes
- helps produce agent docs and context packs

### Codex

- primary implementer
- creates/edits files
- runs tests
- fixes compile/test failures
- should receive strict pass scope, non-goals, and validation checklist

### Claude Web

- architecture/UX reviewer
- second opinion on plans/diffs
- should usually review, not edit
- useful for checking whether implementation matches product/architecture contracts

### Claude Code / Terminal Agent

- repo-aware reviewer or surgical implementer
- good for local scans, diff review, and focused code work
- should not race Codex on the same files

## Multi-Agent Rule

Only one coding agent should modify files at a time.

Reviewer agents should not edit unless explicitly assigned.

Do not let Codex and Claude Code both freely modify the same working tree in parallel. That creates agent soup.

## Recommended Pass Flow

1. Define goal with the product owner and planning agent.
2. Write a precise implementation or review prompt.
3. Include required docs in read-first list.
4. Codex implements or Claude reviews.
5. Agent reports files changed, tests run, failures, and risks.
6. A human manually tests the app/behavior.
7. ChatGPT reviews results/diff/screenshot.
8. Codex performs focused fixes if needed.
9. Commit only after manual test and validation.
10. Update status docs/reports.

## Required Final Report Format for Agents

Every implementation pass should end with this report shape:

```text
# Agent Pass Report

## Pass Name

## Goal

## Files Changed

## Core/Skill/Web/GUI Impact

## User-Facing Changes

## State/Data Changes

## Tests Run

## Manual Smoke

## Deferred Work

## Risks / Known Issues

## Suggested Next Pass
```

Save important reports under:

```text
Docs/Reports/Codex/
Docs/Reports/Claude/
Docs/Reports/Human/
```

## Current Repo Status Snapshot

This status is based on the current conversation and uploaded repo snapshot. Update after each major pass.

### Platform

- Entry is canonical for `skill`, `gui`, and `web`.
- Skill invocation is flattened: `python nspl.py skill <Skill.Name> [args...]`.
- Web apps are discovered under `Web/<Domain>/<App>/web.json`.
- Web apps expose `create_app(context)` and launch through Entry.
- NodeCTX owns durable state routing.

### LifeRPG

Current phase: functional prototype after Pass 2A UX rescue.

What works at prototype level:

- Board launches as `LifeRPG.App`.
- Quick Dump / Inbox exists.
- Deterministic sort exists.
- Quests can be created/started/completed.
- Quest sessions and a shallow expedition simulation exist.
- Habits and Events can be created/managed.
- Settings persist and some affect UI/behavior.
- XP/Tokens ledger exists.
- UI has recovered from the raw CRUD-wall failure into a compact command-center direction.

Known debt:

- expedition simulation is shallow and enemies barely/never meaningfully fight back
- rewards are still placeholder-level
- visual polish is not mockup-grade
- RohTalk is not wired into LifeRPG yet
- sorting is deterministic/template-based, not user-aware
- HTMX OOB updates are functional but simple
- mobile needs dedicated testing/polish
- app UX needs more reward animations and game feel

Immediate likely next LifeRPG passes:

1. visual polish and asset integration hooks
2. better expedition/game simulation
3. RohTalk-backed sorting and Operator Station
4. reward calibration and meaningful progression
5. mobile layout polish

### RohTalk

Current phase: persistent local agent runtime with tool-capable loop, SkillCLI bridge, named toolkits, tracing callbacks, and interactive shell/watch workflows.

Strategic priority: high. RohTalk should become the shared AI/operator substrate used by LifeRPG, DST, and future apps.

Likely next RohTalk needs:

- Web UI / RohTalk app
- app-specific context layering
- better long conversation summarization/maintenance
- structured action proposal/execution for apps like LifeRPG
- stronger tool loop polish for multi-tool updates

### DST / RohBridge

Current phase: game bridge contracts and director tools exist.

Strategic priority: high demo value. DST proves Roh can observe and act in a game loop.

Known direction:

- keep raw command writers away from model-facing tools by default
- use queued writes and result acknowledgments
- improve director behavior with profiles/toolkits
- eventually present DST control/status via Web or RohTalk UI

### AutoRoh

Current phase: generic observed tool-capable loop with DST director profile.

Known direction:

- keep AutoRoh generic
- workflow behavior belongs in profiles/toolkits/director packs
- do not hardcode DST-specific behavior into generic loop code

### Video / LookLab

Current phase: usable GUI vertical slice for frames/video/grading.

Known direction:

- thin GUI shell over shared Core/Skill behavior over time
- unify process/progress handling through Proc where practical
- eventually add Web frontend for video workflows

## Current Development Concerns

### Agent Context Drift

Agents need consistent repo context. Use these docs to avoid re-explaining the architecture every pass.

### UX Quality

Codex can implement technically-correct but poor UX. For product/UI passes, provide a UX contract, mockups, and explicit anti-patterns.

### Hosting

NSPL Web apps can run on a Python-capable server, but public hosting needs auth, permissioning, CSRF protection, deployment docs, and restricted skill exposure.

### State Zips

Do not include `State/`, `__pycache__`, `.git`, `.pytest_cache`, egg-info, or `.pyc` files in agent context zips.

## Prompt Header Template

Use this at the top of future Codex/Claude prompts:

```text
You are working in the NSPLDev repository.

Read first:
- AGENTS.md
- 00_AGENT_HANDOFF.md
- Docs/Agents/00_NSPL_AGENT_BRIEF.md
- Docs/Agents/01_NSPL_ARCHITECTURE_AND_COMMANDS.md
- Docs/Agents/02_PROJECT_CONTEXTS.md
- Docs/Agents/03_AGENT_WORKFLOW_AND_STATUS.md
- Relevant project README files
- Relevant design docs under Docs/Plans/

Follow the repo architecture rules:
- Core owns reusable behavior.
- Skills are thin wrappers.
- Web/GUI are control surfaces.
- NodeCTX owns durable state.
- Use flattened skill invocation.
- Do not touch unrelated domains.
- Add/update tests and README docs for behavior changes.
```
