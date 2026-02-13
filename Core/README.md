# Core

The **Core/** directory contains the foundational, reusable building blocks of NSP Lite.

Code in Core is **infrastructure**, not application logic. It defines stable primitives that other layers depend on, but it does not encode workflows, policies, or opinions about how the system is used.

If a component is intended to be imported, reused, or depended on by multiple skills or applications, it belongs in Core.

---

## Design rules

Core modules follow strict constraints:

- No assumptions about user workflows
- No long-running processes
- No implicit global state
- No side effects at import time
- Fully testable in isolation

Core code should be safe to import, reason about, and reuse without understanding the rest of the system.

---

## What belongs in Core

Examples of appropriate Core responsibilities:

- Filesystem abstractions and durable I/O helpers
- Skill discovery and execution infrastructure
- Task schemas and transition rules
- Runtime context discovery
- Backend-agnostic service clients

---

## What does NOT belong in Core

The following do **not** belong here:

- Concrete user workflows
- One-off scripts
- Opinionated automation logic
- UI concerns
- Application-specific state
- Anything that assumes ChatOps, LLMs, or specific skills exist

Those belong in **Skills/** or in external projects.

---

## Structure

Core is intentionally subdivided:

Core/
    NSPL/ # NSP Lite core primitives
    LLMClient/ # Thin, backend-agnostic LLM client

Each submodule documents its own contract and guarantees.

---

## Dependency direction

Dependencies must flow **outward**:

Skills → Core

Core must never import from Skills.

This constraint keeps the system composable, testable, and safe to evolve.

