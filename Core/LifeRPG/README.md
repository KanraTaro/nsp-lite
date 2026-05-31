# Core/LifeRPG

Core LifeRPG owns the durable state model and app behavior for the first MVP
slice. Skills and Web routes call this package instead of owning business logic.

State is stored through NodeCTX in the Global MVP scope:

```text
State/main/Global/LifeRPG/...
```

Implemented in Pass 1:

- inbox capture and deterministic Roh sorting
- canonical category mapping
- quests, sessions, pause/complete time cards
- simple session-tied expeditions with dynamic allies/enemies arrays
- reward ledger with XP and Leisure Tokens
- default habits and minimal events
- current mission status payload for Web and SkillCLI

Pass 2A adds management services for inbox items, quests, habits, events, and
settings. Settings are persisted under `Config/settings.json` and
`Config/profile.json`; object state remains under the existing LifeRPG NodeCTX
layout.

Pass 2B adds project-aware quest metadata, quest detail payloads, deterministic
Roh next-action guidance, visible quest notes, and session history helpers.
`project` is additive and defaults to `General` for older quest records.

Deferred: live RohTalk, ClickUp, node targeting, conflict resolution,
notifications, advanced party management, Signal Gate/gacha, and Dice/Alea
combat. Early multi-user testing should use separate NSPL instances and ports.
