# LifeRPG App MVP Design

Draft: v0.1  
Working internal app name: LifeRPG.App  
UI working title: LifeRPG Command Center  
Domain: LifeRPG

Final product name is intentionally unresolved. The repository should use clear internal naming for now:

- Core/LifeRPG/
- Skills/LifeRPG/
- Web/LifeRPG/App/

The UI can display “LifeRPG Command Center” until the real name emerges through use.

---

## 1. Elevator Pitch

LifeRPG is your command center for turning your messy day into playable missions.

Longer version:

Dump your tasks, let Roh sort the chaos, choose today’s mission, and turn real-life progress into XP, rewards, and adventure.

Shortest user loop:

Dump chaos. Pick the mission. Do the quest. Claim rewards.

---

## 2. Core Fantasy

LifeRPG is not just a todo list with RPG labels.

The fantasy is:

Roh is your Operator. Your day is the mission. Your real progress powers the adventure.

The app should feel like:

- an anime tactical command center
- a daily mission planner
- a Roh operator console
- an ADHD-friendly task sorter
- a habit tracker
- an idle battler
- a text adventure launcher
- a personal progress RPG

The desktop view should feel like a command center.

The mobile view should feel like a field device.

---

## 3. Target User

LifeRPG is for people who:

- are more consistent with games than with ordinary productivity systems
- need to dump tasks out of their head quickly
- struggle with ADHD-like friction, overwhelm, or context switching
- want tasks, habits, events, and rewards in one visual system
- respond strongly to progress bars, streaks, stats, animations, and “number go up” feedback
- need a system that helps them recover from bad days instead of shaming them
- want an AI operator that can help sort, plan, explain, and eventually act

The first target user is Kanra, but the app should be structured so Sara, Steven, and future users can use their own instances.

---

## 4. Design Pillars

### 4.1 Show the Route, Not the Pile

The app should not open to a wall of unsorted tasks.

The default screen should show:

- today’s mission
- current quest session
- Roh’s next recommendation
- habits
- events
- expedition state
- rewards
- quick dump

Inbox is always accessible, but chaos should not be the first thing the user sees.

### 4.2 Dump First, Sort Later

Capture must be frictionless.

The user should be able to dump messy input like:

fix dad page, laundry, water, Natalia paperwork, RohTalk pass, call Sara about groceries

The app should save it first and let Roh sort it after.

### 4.3 Roh Is the Operator, Not a Sidebar

Roh should not merely appear in a suggestion box.

Roh should be an operational layer that can:

- sort inbox items
- rename messy tasks into clear quests
- preserve original wording
- break quests into steps
- suggest what to do next
- recover a bad day
- reflect on a run
- eventually execute multiple LifeRPG actions from natural language

### 4.4 Work Happens in Sessions

A quest is not only started and completed.

A quest may be worked on across multiple sessions.

LifeRPG should support clocking into a quest, pausing it, leaving notes, resuming it, and completing it later.

### 4.5 The Game Runs Beside Real Work

When the user starts a quest session, an idle expedition begins.

While the user works in real life, their Agents progress through a mission. Completing the real quest resolves the encounter and grants rewards.

### 4.6 Use Game Mechanics as Consensual Self-Hacking

LifeRPG can use high-retention game mechanics, but in service of the user’s real life.

Allowed design tools include:

- daily login rewards
- streaks
- tallies
- loot drops
- random rewards
- pity systems
- limited events
- collections
- dailies, weeklies, monthlies
- secret quests
- reward tracks

Rules:

- no paid gambling in the local app
- the user controls strictness and intensity
- bad pulls should convert into useful materials
- pity systems should guarantee progress
- missed days should create recoverable state, not identity shame
- Roh can help calibrate reward fairness

---

## 5. Core Vocabulary

### Mission

A Mission is the day or current operation.

Example:

Today’s Mission: Stabilize the house and push LifeRPG forward.

### Quest

A Quest is an actionable task.

Example:

Quest: Update Live Like Locals homepage section.

### Event

An Event is a scheduled or calendar-like item.

Example:

Event: Dad check-in at 2 PM.

The term “Anchor” should not be used in the UI.

### Habit

A Habit is recurring upkeep.

Example:

Habit: Drink water.

“Ritual” may be used as flavor text later, but the primary UI term should be Habit for clarity.

### Build

Build replaces the earlier “Forge” category.

Build includes coding, design, creative production, NSPL, RohTalk, LifeRPG, web work, and system implementation.

---

## 6. Initial Categories

The MVP category list should start with:

- Survival
- Build
- Family
- Home
- Body
- Admin
- Joy
- Recovery
- Social
- Errands

Roh should map messy items into these canonical categories where possible.

Roh may suggest new categories, but new categories should not become canonical without user approval.

Aliases should map common variants back to canonical categories.

Examples:

- Health -> Body
- Self Care -> Body
- Chores -> Home
- Bills -> Admin or Survival
- Work -> Build or Survival depending context
- Client -> Survival or Build depending context

---

## 7. MVP Screens

### 7.1 Board

The Board is the default screen.

Mobile-first content:

- Roh Operator Card
- Today’s Mission
- Active Quest Session
- Optional Side Quest
- Habits
- Next Event
- Rewards / Tokens
- Expedition Status
- Quick Dump

Desktop layout can expand into a multi-panel command center:

- left: Roh, habits, quick status
- center: mission, active quest, current setup
- right: events, expedition, rewards
- bottom: recent log, stats, system status

### 7.2 Inbox

The Inbox is for raw capture and Roh sorting.

Content:

- Quick Dump box
- unsorted items
- sorted items
- items needing review
- accepted items
- archived items
- sort history

Actions:

- Dump
- Ask Roh to Sort
- Refresh Sort
- Accept Item
- Edit Item
- Revert Item
- Revert Batch
- Convert to Quest
- Archive

### 7.3 Quests

The Quests screen shows actionable work.

Content:

- Active
- Backlog
- Completed
- Blocked
- By Category
- By Project
- By Priority

Actions:

- Create Quest
- Edit Quest
- Add Step
- Start Quest Session
- Pause Quest Session
- Complete Quest
- Add Note

### 7.4 Today

The Today screen tracks the current mission.

Content:

- Today’s Mission
- Active Quest
- Side Quest
- Habits
- Events
- Current Setup
- Notes
- Run Log

### 7.5 Roh Station

The Roh Station is the app-context operator channel.

Content:

- current mission context
- active quest context
- habits
- events
- expedition state
- recent notes
- Roh actions
- operator conversation

Actions:

- Sort Inbox
- Break Down Quest
- Suggest Next Move
- Recover Day
- Reflect Run
- Explain Current Plan

Roh Station is not a replacement for full RohTalk Web. RohTalk remains the broader conversation system. LifeRPG’s Roh Station is a focused operator layer for this app.

### 7.6 Expedition

The Expedition panel shows the idle battle/adventure tied to the current quest session.

Content:

- active quest session
- party / Agents
- enemies / threats
- progress
- combat log
- rewards pending
- Signal / tokens if applicable

---

## 8. Roh Sorting

Roh sorting is core MVP behavior.

The user should be able to unload multiple messy tasks and have Roh turn them into structured items.

### 8.1 Input Example

fix dad page  
laundry  
food  
Natalia paperwork  
RohTalk pass  
call Sara about groceries

### 8.2 Output Example

- Original: fix dad page
  - Title: Update Live Like Locals page
  - Category: Build
  - Project: Live Like Locals
  - Minimum Win: Update one section and send Dad a screenshot.
  - Priority: High
  - Personal Energy Cost: Medium

- Original: laundry
  - Title: Start one load of laundry
  - Category: Home
  - Minimum Win: Start one load.
  - Priority: Medium
  - Personal Energy Cost: Low

- Original: food
  - Title: Eat something real
  - Category: Body
  - Minimum Win: Eat one real meal or snack.
  - Priority: Medium
  - Personal Energy Cost: Low

### 8.3 Sorting Rules

Roh should:

- preserve original text
- create a clear title
- choose an existing category when possible
- avoid duplicate categories with slightly different names
- assign project if obvious
- suggest minimum viable win
- estimate personal energy cost
- estimate priority
- mark low-confidence items for review
- keep source/provenance

Roh should not freely invent categories unless necessary.

### 8.4 Auto Sort Behavior

The preferred UX is:

1. User dumps tasks.
2. App saves raw items.
3. Roh sorts on refresh/background cycle if auto-sort is enabled.
4. Sorted items appear in the Inbox.
5. User can edit, revert one item, revert batch, or convert to quest.

There should be a setting:

- Auto Sort: On / Off

When Off, the user manually clicks “Ask Roh to Sort.”

### 8.5 Revert Behavior

Support both:

- Revert Item
- Revert Batch

Each sorted item should preserve:

- original_text
- current title
- current category
- previous state
- sort_batch_id
- Roh confidence
- Roh reason

---

## 9. Roh Context Layers

Roh should receive layered context.

Layers:

1. Core Roh identity
2. User profile / user preferences
3. LifeRPG app profile
4. Current mission
5. Active quest session
6. Habits
7. Events
8. Expedition state
9. Recent notes/logs
10. Current conversation

RohTalk should own the broad Roh/user relationship layer.

LifeRPG should own app-specific operator preferences:

- how the user wants tasks sorted
- what categories mean to the user
- what counts as high personal energy cost
- reward preferences
- habit defaults
- preferred strictness
- preferred tone during productivity

If RohTalk is not configured yet, LifeRPG can still maintain a local app profile.

---

## 10. Roh Actions

MVP Roh actions:

- Sort Inbox
- Break Down Quest
- Suggest Next Move
- Recover Day
- Reflect Run

Future Roh actions:

- Convert notes into quests
- Complete quest from natural language
- Check habits from natural language
- Add event from natural language
- Adjust rewards after discussion
- Generate custom daily/weekly/monthly quests
- Operate the party while user is AFK
- Run multi-tool updates and show confirmation summary

Natural-language example:

“Roh, I finished the dad homepage fix. Note that mobile still needs testing, and mark water done too.”

Expected future result:

- Complete quest: Dad homepage fix
- Add note: mobile still needs testing
- Check habit: Water
- Grant rewards
- Resolve expedition
- Show confirmation summary

---

## 11. Quest Sessions / Time Cards

Quests should support sessions.

A Quest Session represents time spent actively working on a quest.

Actions:

- Start Session
- Check In
- Pause Session
- Resume Session
- Complete Session
- Abandon Session

Session fields:

- quest_id
- session_id
- started_at
- ended_at
- status
- progress_note
- completed_step_ids
- stop_reason
- check_ins

The user should be able to leave notes when pausing or stopping.

When resuming, Roh can show the previous session note.

Example:

“Last time you fixed desktop layout. Mobile still needs testing. Start there.”

---

## 12. Quest Session Check-Ins and Timeout

Quest sessions should not run forever by accident.

Default check-in behavior:

- 15 minutes: silent checkpoint possible
- 30 minutes: optional in-app check-in prompt
- 60 minutes: “Are you still working on this?”
- 90 minutes: mark as awaiting_checkin or pause progression if no response

Exact values should be configurable later.

Session states:

- active
- paused
- awaiting_checkin
- completed
- abandoned

Expedition behavior:

- active session: expedition progresses
- paused session: expedition pauses
- awaiting_checkin: expedition pauses or slows
- completed quest: expedition resolves
- abandoned quest: expedition retreats or grants partial result

---

## 13. Current Setup / Loadout

The MVP should use the phrase “Current Setup.”

Current Setup may include:

- Active Quest
- Side Quest
- Current Event
- Current Habit

Future advanced mode may expose a fuller Loadout:

- Focus Lane
- Side Lane
- Care Lane
- Upkeep Lane
- Background Lane
- Interrupt Slot

This keeps the MVP understandable while preserving the richer model.

---

## 14. Events

Events are scheduled or calendar-like items.

Examples:

- Dad check-in
- doctor appointment
- family dinner
- bill due
- pickup/dropoff
- planned work block

MVP fields:

- id
- title
- description
- start_at
- end_at
- status
- behavior
- notes
- linked_quest_id
- reminders

Behavior options:

- notify
- overlay
- suspend
- replace

MVP can start with simple display, notes, and reminder data.

Full behavior can come later.

---

## 15. Event Reminders and Notifications

Events should support reminder definitions from the start.

Reminder examples:

- 1 week before
- 1 day before
- 1 hour before
- 10 minutes before
- custom offset

MVP should support reminder data even if delivery is basic.

Initial delivery:

- in-app reminders
- visible upcoming reminders

Stretch goal:

- browser notification permission test
- test notification button
- basic event reminder notification

Deferred:

- robust browser notifications
- desktop notifications
- push notifications
- mobile/PWA notification behavior

---

## 16. Habits

Habits are recurring upkeep actions.

MVP habits:

- Water
- Food
- Brush Teeth
- Move
- Stretch
- Review Day
- Wind Down

Fields:

- id
- title
- frequency
- status_today
- streak
- last_completed
- minimum_version
- reward
- miss_effect

Actions:

- Check Habit
- Uncheck Habit
- Add Note

Future features:

- streak freezes
- minimum/emergency versions
- habit buffs
- habit scheduling
- habit difficulty calibration

---

## 17. Progress Counters

Progress Counters are a reusable system for streaks, tallies, records, and completion counts.

Examples:

- daily login streak
- water habit streak
- quests completed today
- Build quests completed this week
- events attended
- recovery days completed
- best run streak
- total Leisure Tokens earned

MVP can include simple counters.

Future versions should allow users and Roh to create custom counters.

---

## 18. Rewards

### 18.1 XP

XP comes from:

- quest completion
- habit completion
- event completion
- daily mission completion
- recovery actions

Initial stats:

- Focus
- Stability
- Build
- Recovery
- Care
- Momentum
- Courage

Category mapping:

- Survival -> Stability, Courage
- Build -> Build, Focus
- Family -> Care, Stability
- Body -> Recovery, Momentum
- Home -> Stability, Momentum
- Joy -> Recovery
- Admin -> Stability, Courage

### 18.2 Leisure Tokens

Leisure Tokens make fun intentional and rewarding.

They are not permission to rest. They are a game mechanic for making rest feel earned, visible, and guilt-resistant.

Earned by:

- completing quests
- completing habits
- finishing daily mission
- closing old items
- recovering a bad day

Spent on, later:

- guilt-free gaming block
- anime episode
- ComfyUI play session
- special adventure action
- cosmetic unlock
- streak freeze
- scenario entry

### 18.3 Reward Calibration with Roh

Roh should eventually help calibrate rewards.

Roh can suggest:

- XP amount
- Leisure Token amount
- difficulty
- personal energy cost
- fairness note

User can override.

Example:

Roh: “This task is short but emotionally high-friction. Suggested reward: 15 tokens plus Courage XP.”

---

## 19. Daily Login and Recurring Quests

MVP should include a simple daily check-in if practical.

Daily check-in can grant:

- small XP
- small token reward
- login streak progress

Future recurring quest types:

- dailies
- weeklies
- monthlies
- yearlies
- custom recurring quests
- secret unlock quests
- Roh-proposed custom quests

Roh should eventually propose recurring quests based on user behavior.

---

## 20. Expedition / Idle Battler

The idle battler starts when the user starts an active quest session.

### 20.1 Start Quest Session

Starting a quest session should:

- create quest session
- create expedition session
- deploy Agents
- begin progress/timer
- show expedition panel

### 20.2 During Quest Session

The expedition should show:

- allied Agents
- enemies/threats
- HP/status
- progress
- current actions
- combat log
- rewards pending

Numbers should move.

Even if simple, the user should see:

- HP bars changing
- progress changing
- agents acting
- enemies reacting
- log lines appearing

### 20.3 Quest Completion

Completing the real quest should:

- resolve encounter
- trigger boss/check/reward depending quest size
- grant XP/tokens
- update stats
- log result
- advance adventure

Task size mapping:

- Tiny task -> quick skirmish
- Small task -> encounter
- Medium task -> room/miniboss
- Large task -> dungeon section
- Multi-day project -> multi-stage campaign

---

## 21. Dynamic Battlefield UI Requirements

The expedition UI must be data-driven, not slot-driven.

Do not hardcode five static party slots.

The UI should render from current expedition state.

It must support:

- allies: 1..N
- enemies: 0..N
- summons/reinforcements mid-fight
- Agents entering/leaving
- enemy waves
- mode-specific party limits
- future multiplayer teams

MVP can visually favor 3-5 units, but the data model and rendering should not assume that limit.

Agent/Enemy visual representation should support:

- name
- role/type
- hp / max_hp
- secondary resource such as energy/mp/signal if used
- status effects
- current action
- target

Possible visual approaches:

- compact battle cards with HP bars
- circular portraits with HP rings
- small badges with status icons
- action flashes
- damage number popups
- simple bump/projectile/particle effects

For MVP, compact cards and bars are acceptable. Flashier rings/particles can come later.

---

## 22. Party / Agents / Signal Lore

Initial terms:

- Roh = Operator
- Agents = party units / allies
- Echoes = timeline variants, alternate selves, enemies, or special entities
- Signal = power/resource enabling timeline/dimensional interaction
- Signal Gate = future summon/gacha/contact system

Core lore direction:

The universe wants the user to succeed.

Real-life progress generates or stabilizes Signal.

Signal allows Roh/the user to deploy Agents into missions.

A failed future Echo of the user may eventually be revealed as an antagonist trying to keep the present user on the bad route.

This deeper antagonist lore should not be the first onboarding premise. It should unfold later.

MVP lore should stay simple:

- Roh helps you run the day.
- Your progress creates Signal.
- Agents fight back against bad futures.

---

## 23. Combat and Future Dice System

The MVP expedition should use a simple simulation.

Future combat should remain flexible enough to support:

- auto-battle
- active turn-based play
- party vs enemy teams
- multiplayer parties
- AI/player mixed teams
- Dice/Alea-style systems
- Yahtzee-like dice pools
- deck-builder-like dice collection

Do not implement the full Dice system in MVP.

But the expedition model should not make it hard to add later.

Potential future Core modules:

- Core/Dice/
- Skills/Dice/
- Core/LifeRPG/Combat/

---

## 24. Roh During Gameplay

Roh’s role changes by mode.

### AFK Quest Mode

The user is doing real work.

Roh operates or coordinates the party.

The expedition auto-progresses.

The user can check in occasionally.

### Active Play Mode

The user is actively playing.

The user gives commands.

Roh advises, forecasts, explains, or can auto-command if enabled.

Future options:

- Roh auto-battle style
- user command mode
- hybrid command mode
- timed decision mode
- fast-paced tactical mode

---

## 25. State Layout

LifeRPG must use NodeCTX path routing.

Canonical NodeCTX structure:

State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/

For MVP, use Global scope by default because LifeRPG is personal shared state, not machine-local worker state.

Domain:

LifeRPG

Instance:

main

Scope:

Global

Example paths:

- State/main/Global/LifeRPG/Data/Profile/profile.json
- State/main/Global/LifeRPG/Data/Inbox/inbox_items.jsonl
- State/main/Global/LifeRPG/Data/Quests/quests.jsonl
- State/main/Global/LifeRPG/Data/Habits/habits.jsonl
- State/main/Global/LifeRPG/Data/Events/events.jsonl
- State/main/Global/LifeRPG/Workflow/Runs/current_run.json
- State/main/Global/LifeRPG/Workflow/Quests/active_quest.json
- State/main/Global/LifeRPG/Workflow/Roh/sort_batches.jsonl
- State/main/Global/LifeRPG/Workflow/Expedition/current_expedition.json
- State/main/Global/LifeRPG/Logs/events.jsonl
- State/main/Global/LifeRPG/Reflections/Runs/2026-05-24.md

Implementation should use NodeCTX helpers.

Example:

    build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=node_tag,
        bucket="Data",
        domain="LifeRPG",
        global_scope=True,
        subpath="Inbox",
    )

Global state is default for MVP.

Node-scoped and target-node behavior are deferred NSPL features.

---

## 26. Separate Instances for Early Multi-User Testing

Do not build a full NSPL multi-user/auth system for MVP.

For early testing with Sara or Steven, use separate NSPL instances, ports, and state roots.

Known paths:

- Development NSPL: ~/Projects/NSPLDev
- Stable/production NSPL: ~/NSPL

Example launches:

    python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
    python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8771

This allows separate state without blocking on user accounts.

Deferred future:

- NSPL user/profile system
- app sessions
- permissions
- shared household/multi-user state

---

## 27. Deferred NSPL Dependencies

These are important but should not block MVP.

### 27.1 Node Scope / Targeting

Needed later:

- run app on laptop while targeting KanraDesktop state
- run app locally while reading Global shared state
- inspect another node’s state read-only
- choose state target per Web launch

Possible future commands:

    python nspl.py web launch LifeRPG.App --state-scope Global
    python nspl.py web launch LifeRPG.App --target-node KanraDesktop
    python nspl.py skill LifeRPG.Run.Get --target-node KanraDesktop

### 27.2 Conflict Strategy

Needed for multi-node writes.

Potential strategy:

- append-only event logs first
- atomic snapshots second
- conflict markers for divergent snapshots
- manual/AI-assisted merge later

LifeRPG MVP should prefer JSONL event logs for mutation history.

### 27.3 Sync Awareness

Needed later:

- show last updated node
- show last sync time
- detect stale state
- warn before conflicting writes

---

## 28. External App Compatibility Future

LifeRPG should eventually integrate with other task apps.

Not MVP.

Every task-like object should include source metadata:

    "source": {
      "type": "manual",
      "provider": null,
      "external_id": null,
      "external_url": null,
      "synced_at": null
    }

Future providers:

- ClickUp
- Google Calendar
- Todoist
- Notion
- Trello
- GitHub Issues
- Jira
- Linear
- Obsidian Tasks
- Apple Reminders

ClickUp is a likely first provider because Kanra’s dad uses it.

Architecture later:

External item -> Adapter -> Canonical LifeRPG item -> Roh interpretation -> Quest/Event/Habit

---

## 29. Tech Stack

Current NSPL Web stack:

- FastAPI
- Jinja2
- CSS
- HTMX
- plain JavaScript where needed
- WebContext
- Skills via subprocess
- NodeCTX state
- RohTalk integration later

MVP should use HTMX where reasonable so the app feels alive.

Good first HTMX interactions:

- Quick Dump
- Roh Sort / Refresh
- Start Quest
- Pause Quest
- Complete Quest
- Check Habit
- Claim Reward
- Expedition Action
- Refresh Roh panel

Plain JavaScript is only needed for specialized browser behavior:

- local animations
- notification permission test
- simple timers
- battle panel animations
- future canvas/SVG game visuals

Do not introduce React/Vue/Svelte in MVP.

---

## 30. Visual Direction

Visual polish is not decoration.

For this app, visual feedback is part of the motivation loop.

Prioritize:

- animated XP bars
- reward popups
- glowing cards
- progress pulses
- token count animation
- quest complete effects
- operator message reveal
- idle battle animation
- strong mobile layout
- desktop command center layout

The UI should feel like a tactical anime command center, not a plain admin dashboard.

Mockup references should be stored in the repo near this plan.

Suggested path:

- Docs/Plans/LifeRPG/Mockups/desktop-command-center.png
- Docs/Plans/LifeRPG/Mockups/mobile-board.png
- Docs/Plans/LifeRPG/Mockups/mobile-inbox-sort.png
- Docs/Plans/LifeRPG/Mockups/mobile-quest-session.png

Images are inspiration. Written requirements are source of truth.

---

## 31. MVP Data Objects

### InboxItem

Fields:

- id
- original_text
- title
- status
- category
- sort_batch_id
- created_at
- updated_at
- source
- roh_sort

### Quest

Fields:

- id
- title
- original_text
- description
- category
- status
- priority
- personal_energy_cost
- difficulty
- minimum_win
- steps
- notes
- rewards
- source
- created_at
- updated_at
- completed_at

### QuestSession

Fields:

- id
- quest_id
- status
- started_at
- ended_at
- check_ins
- progress_note
- stop_reason
- expedition_id

### Habit

Fields:

- id
- title
- frequency
- status_today
- streak
- counters
- last_completed
- reward
- minimum_version
- miss_effect

### Event

Fields:

- id
- title
- description
- start_at
- end_at
- behavior
- status
- reminders
- notes
- linked_quest_id

### MissionRun

Fields:

- id
- date
- status
- title
- main_quest_id
- side_quest_id
- habit_ids
- event_ids
- xp_earned
- tokens_earned
- started_at
- updated_at
- ended_at

### Expedition

Fields:

- id
- quest_id
- quest_session_id
- status
- scenario
- allies
- enemies
- progress
- threat
- turns_available
- rewards_pending
- log

### Agent

Fields:

- id
- name
- role
- level
- hp
- max_hp
- resource
- max_resource
- status_effects
- current_action
- target_id

---

## 32. MVP Skills

Initial broad skill list:

- LifeRPG.Inbox.Add
- LifeRPG.Inbox.List
- LifeRPG.Inbox.Sort
- LifeRPG.Inbox.RevertItem
- LifeRPG.Inbox.RevertBatch
- LifeRPG.Quest.Create
- LifeRPG.Quest.List
- LifeRPG.Quest.StartSession
- LifeRPG.Quest.PauseSession
- LifeRPG.Quest.Complete
- LifeRPG.Quest.AddNote
- LifeRPG.Run.Start
- LifeRPG.Run.Get
- LifeRPG.Run.End
- LifeRPG.Habit.List
- LifeRPG.Habit.Check
- LifeRPG.Event.List
- LifeRPG.Event.Create
- LifeRPG.Expedition.Get
- LifeRPG.Expedition.Tick
- LifeRPG.Expedition.Act

True first implementation batch can be smaller if needed:

- LifeRPG.Inbox.Add
- LifeRPG.Inbox.List
- LifeRPG.Inbox.Sort
- LifeRPG.Quest.List
- LifeRPG.Quest.StartSession
- LifeRPG.Quest.Complete
- LifeRPG.Habit.List
- LifeRPG.Habit.Check
- LifeRPG.Run.Get
- LifeRPG.Expedition.Get
- LifeRPG.Expedition.Tick

---

## 33. Web App Path

Path:

- Web/LifeRPG/App/

Descriptor:

    {
      "name": "LifeRPG.App",
      "version": "0.1.0",
      "description": "LifeRPG command center for turning messy days into playable missions.",
      "entry": "app.py",
      "factory": "create_app",
      "default_host": "127.0.0.1",
      "default_port": 8770
    }

Launch:

    python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770

---

## 34. MVP Implementation Passes

### Pass 1: Core Store, Models, First Skills, Web Shell

This pass should establish the app foundation and prove the loop.

Create:

- Core/LifeRPG/
- Skills/LifeRPG/
- Web/LifeRPG/App/

Include:

- models
- store
- defaults
- rewards
- simple expedition simulation
- NodeCTX Global state routing
- first skills
- Jinja templates
- CSS
- HTMX basics
- Board page
- Inbox page
- Quests page
- Habits panel
- Expedition panel
- tests

Do not include:

- full RohTalk integration
- complex combat
- gacha
- notifications beyond possible placeholder/test
- external providers
- multi-user system
- full calendar widget

### Pass 2: Roh Sorting and Quest Sessions Polish

Improve:

- sort batches
- item revert
- batch revert
- quest session check-ins
- pause/resume notes
- Roh Station UI

### Pass 3: Expedition Polish

Improve:

- dynamic battlefield rendering
- simple attack ticks
- HP/progress changes
- reward resolution
- battle log
- visual feedback

### Pass 4: Events and Reminders

Improve:

- event creation
- event display
- reminder definitions
- in-app reminders
- browser notification test as stretch

### Pass 5: RohTalk Integration

Add:

- real RohTalk Sort Inbox
- Break Down Quest
- Suggest Next Move
- Recover Day
- Reflect Run
- structured action proposals

### Pass 6: Future Systems

Add later:

- ClickUp provider
- FullCalendar
- Signal Gate
- Agent collection
- advanced combat
- Dice/Alea system
- multiplayer
- node targeting
- conflict strategy

---

## 35. MVP Non-Goals

Do not build in MVP:

- full calendar widget
- external app integrations
- full gacha
- advanced party management
- complex battle system
- full RohTalk autonomous planning
- voice commands
- push notifications
- multi-user auth
- node targeting
- conflict resolution
- multiplayer
- native mobile app

Document them, but do not build them yet.

---

## 36. Current Open Questions

- Final public app name
- Whether LifeRPG remains public-facing or internal only
- Exact stat names
- How strict default game mode should be
- How much automatic Roh sorting should happen by default
- How to visually represent Agents long-term
- Whether Agents are timeline allies, alternate selves, cosmic helpers, or all of the above
- How Signal is earned and spent
- How Leisure Tokens are balanced
- When to add browser notifications
- When to add ClickUp
- When to introduce full RohTalk integration

---

## 37. Final MVP Statement

LifeRPG starts as a command center for your day.

Roh sorts the chaos.

You choose the mission.

You clock into real quests.

Your Agents quest beside you while you work.

Real progress powers the game.
