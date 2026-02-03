# Config

This directory contains **persistent, user-authored configuration** for NSPL-based systems.

Unlike `State/`, which is expected to be **ephemeral and disposable during development**, `Config/` is intended to survive wipes, test resets, and node restarts.

If `State/` is deleted, the system should always be able to fall back to `Config/` and continue operating with sane defaults.

---

## Purpose

`Config/` exists to hold:

* Long-lived defaults
* User intent
* Human-authored preferences
* Stable system identity (personas, library roots, model preferences, etc.)

Nothing in this folder should be auto-generated without explicit user intent.

---

## What belongs here

Typical examples:

* Default personas
* Library root configuration
* LLM client defaults
* RohTalk behavior settings
* Feature flags or policy-level toggles

Example layout:

```
Config/
├── LLMClient/
│   └── defaults.json
├── RohTalk/
│   └── personas.json
├── Library/
│   └── library.json
```

All files here should be:

* Human-readable
* Safe to edit manually
* Reasonably stable over time

---

## What does NOT belong here

Do **not** store:

* Runtime state
* Derived artifacts
* Logs
* Temporary overrides
* Per-run scratch data

Those belong under `State/`.

---

## Relationship to State/

`State/` is expected to change constantly.

During development, it is common (and encouraged) to wipe `State/` entirely.

When configuration needs to be overridden at runtime, the **canonical override path** is:

```
State/<InstanceId>/<Scope>/Config/<Domain>/...
```

Example overrides:

```
State/main/Global/Config/LLMClient/defaults.json
State/main/KanraDesktop/Config/Library/library.json
```

Load precedence should always be:

1. `State/<Instance>/<Scope>/Config/...`
2. `Config/...`
3. Hard-coded defaults (last resort only)

---

## Design principle

* `Config/` expresses **intent**
* `State/` expresses **activity**

If you delete `State/` and the system breaks permanently, something that belongs in `Config/` was put in the wrong place.
