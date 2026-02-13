# NSPL Skills

**Skills/NSPL** contains reference skills that ship with NSP Lite itself.

These skills demonstrate correct usage of Core primitives and provide essential system functionality.

They are not application-specific and are safe to study, reuse, or modify.

---

## What lives here

NSPL skills fall into two categories:

### Infrastructure skills

Skills that expose core system behavior:

- ChatOps.send_task
- ChatOps.run_worker
- ChatOps.queue_status

These are the primary interface for filesystem-backed automation.

---

### Diagnostic and test skills

Simple, deterministic skills used for validation:

- Tools.Echo.echo
- Tools.Time.now
- Tools.TestFail.fail

These exist to:
- Verify pipelines
- Test workers
- Debug state transitions
- Provide known-good behaviors

They are intentionally minimal.

---

## What does NOT live here

This directory is **not** for:

- User workflows
- Application logic
- Domain-specific automation
- Long-term business logic

Those belong in separate skill domains or external projects.

---

## Why this exists

Shipping these skills with NSP Lite ensures:

- A working system out of the box
- Deterministic demos and tests
- Stable reference implementations
- A clear boundary between framework and user code

You can remove or replace these skills in your own deployments without breaking Core.

