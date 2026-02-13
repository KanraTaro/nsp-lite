# Skills

The **Skills/** directory contains executable entrypoints for NSP Lite.

Skills are the *buttons* of the system. They are how users, scripts, workers, and tools interact with Core primitives.

Every skill is invoked through **SkillCLI**.

---

## What a skill is

A skill is:

- A small, explicit unit of behavior
- Discovered via `skill.json`
- Executed exactly once per invocation
- Stateless beyond the filesystem
- Responsible only for its own task

Skills should be easy to read, easy to test, and easy to delete.

---

## What skills do

Skills typically:

- Read arguments
- Use `ctx.node_ctx` for durable I/O
- Call into Core modules
- Print user-facing output
- Return an exit code

They should *not* manage lifecycle, logging infrastructure, or environment setup.

---

## Structure

Skills/
    <Domain>/
        <SkillName>/
            skill.json
            skill.py

Domains group related skills but do not imply hierarchy or ownership. <SkillName> dirs can also be nested further for deeper organization.

---

## Design constraints

Skills must follow these rules:

- Executed only via SkillCLI
- No direct filesystem writes outside NodeCTX
- No background threads or loops
- No global mutable state
- No imports from other skills

If logic grows large or reusable, it belongs in **Core/** instead.

---

## Philosophy

Skills are intentionally boring.

They exist to expose Core capabilities in a safe, testable, observable way.

Complexity lives in composition, not in individual skills.

