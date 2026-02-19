# NSPL Core

**Core/NSPL** contains the core primitives that define *NSP Lite* itself.

These modules are framework infrastructure. They establish the execution model, filesystem layout, and durability guarantees that everything else builds on.

Nothing in this directory is a “skill.”

---

## Modules

### SkillCLI

The canonical dispatcher for executing skills.

Responsibilities:
- Discover skills via `skill.json`
- Construct a stable runtime context
- Invoke exactly one skill per execution
- Emit structured execution logs

SkillCLI is the only supported entrypoint for running skills.

---

### NodeCTX

Filesystem and logging utilities used by all durable operations.

Responsibilities:
- Canonical state and log paths
- Atomic JSON writes
- JSONL append with rotation and throttling
- Best-effort logging guarantees

All filesystem writes that represent state or logs must go through NodeCTX.

---

### ChatOps (core)

Filesystem-backed task queue primitives.

Responsibilities:
- Task schema validation
- Queue directory layout
- Atomic claim and transition logic
- Durable task finalization rules

This module defines the *protocol*, not the user interface.

---

### ProjectRoot

Runtime root discovery utilities.

Responsibilities:
- Locate the effective project root
- Ensure consistent behavior regardless of invocation location
- Support test isolation and tooling

---

## What this layer guarantees

Core/NSPL provides:

- Crash-safe behavior via filesystem primitives
- Inspectable, replayable state
- Deterministic execution boundaries
- No hidden background services
- No reliance on databases or brokers

---

## What this layer does not do

Core/NSPL does **not**:

- Define user workflows
- Run long-lived daemons
- Enqueue tasks on its own
- Execute skills directly

Those behaviors live in **Skills/** and in consuming applications.

___

### Portability Contract

Core/NSPL follows a strict portability contract:

* Core/NSPL must remain **stdlib-first**

  * No GUI frameworks
  * No heavyweight native dependencies
  * No platform-specific assumptions
* All Core/NSPL functionality must work on:

  * Linux
  * macOS
  * Windows
  * Headless systems (e.g. servers, SBCs)
* External tools (ffmpeg, Ollama, etc.) are **optional integrations**

  * Availability must be checked explicitly
  * Absence must degrade gracefully
* GUIs are **shells**, not execution engines

  * All durable logic must live in Core or Skills
  * GUIs may observe state or invoke SkillCLI / Proc
* No background services

  * All execution must be explicit and inspectable
* Filesystem state is the integration boundary

  * CLI, GUI, and agents must interoperate through shared artifacts, not private APIs

Violating this contract requires an explicit design decision and documentation.

---

## Datastores & Indexing Policy (Filesystem Truth)

NSPL is **filesystem-truth first**.

### Source of truth
If something must be:
- durable across crashes
- inspectable by humans/tools
- replayable for debugging
- syncable between machines

…then it must exist as a **file artifact** under `State/` (JSON snapshots + JSONL event logs).

### Optional databases
Databases are allowed, but only as **derived projections** (indexes/caches) that can be rebuilt from file artifacts.

Use a DB when we need:
- fast search across many artifacts
- aggregation / analytics queries
- UI responsiveness on large datasets

Rules:
- DB contents are **never the only copy** of important state.
- If the DB is deleted/corrupted, the system must be able to regenerate it from artifacts.
- Multi-writer shared state should prefer **append-only logs + projections** over “shared mutable JSON”.

### Concurrency guidance
- Prefer **single-writer per artifact**.
- For many writers, write **events** (append-only) and rebuild projections.
- Avoid shared mutable files that will cause sync conflicts.

---

