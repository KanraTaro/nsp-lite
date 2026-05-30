# NodeCTX State Guide

NodeCTX routes durable runtime state. State is not source code and should not be committed.

## Canonical Layout

```text
State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/
```

Example:

```text
State/main/Global/LifeRPG/Data/Quests/<quest_id>.json
State/main/Global/RohTalk/Workflow/Conversations/<conversation_id>.json
```

## Buckets

- `Config`: settings, profiles, provider/app configuration.
- `Data`: durable domain objects such as quests, habits, events, conversations, records.
- `Workflow`: operational state such as active sessions, queues, proposals, ledgers.
- `Logs`: JSONL event/audit logs.
- `Reflections`: summaries, reviews, and longer interpreted artifacts.

## Scope

Use `Global` when state should be shared for the instance.

Use a node scope when state belongs to one machine or node. Node targeting and conflict handling are not complete platform features yet, so do not fake multi-node semantics in app code.

## Rules

- Use NodeCTX/store helpers for durable state.
- Do not construct ad hoc `State/` paths in product code.
- Do not put source docs, generated bundles, or committed fixtures under runtime `State/`.
- Exclude `State/` from public zips and commits.

## Known Debt

NodeCTX provides atomic writes, but broader read-modify-write flows can still lose updates under concurrent writers. Treat multi-process mutation as a known hardening area until a stronger conflict strategy exists.
