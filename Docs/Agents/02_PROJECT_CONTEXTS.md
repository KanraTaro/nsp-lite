# NSPL Project Contexts

## Platform Spine: Core/NSPL

`Core/NSPL` contains the platform spine:

- Entry gateway and command surfaces
- Web app discovery and launching
- SkillCLI compatibility and skill loading
- GUICLI compatibility and GUI discovery
- NodeCTX durable state routing
- ProjectRoot resolution
- Proc execution abstractions
- Deps helpers
- ChatOps task queue primitives

The current strategic direction is that Entry remains canonical and compatibility packages remain importable but should not drive new syntax or docs.

## NodeCTX

NodeCTX is the authoritative durable-state routing layer.

Canonical state layout:

```text
State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/
```

NodeCTX provides:

- canonical path building
- bucket normalization
- safe reads/writes
- atomic JSON/text/bytes writes
- JSONL append and logging helpers
- optional filename prefixing for provenance

NodeCTX is foundational to NSP/FPP-style observable state. Do not bypass it for durable app state.

## RohTalk

RohTalk is a persistent local agent runtime and tool-capable conversation system.

It provides:

- durable multi-turn conversations stored through NodeCTX
- normalized conversation/message storage with assistant tool calls and tool result messages
- append-only event logs alongside metadata JSON
- backend-agnostic conversation design where RohTalk stores normalized messages and LLMClient handles backend details
- streaming support through `LLMClient.chat_stream_collect` in tool-capable turns
- a `run_turn` orchestration seam that selects plain chat or tool-capable chat
- a `tool_loop` that can run iterative model/tool steps until a final response or max-step failure
- SkillCLI tool execution bridge for model-facing tools mapped to canonical skills
- named toolkits such as `basic` and `dst_director`
- optional console tracing callbacks for tool-loop steps, calls, and results
- CLI skills for start/chat/oneshot/list/show/delete/clear/tool testing
- `RohTalk.shell` for persistent interactive conversations, optional tool mode, read-only watch mode, and `/note` injection

State lives under NodeCTX, broadly:

```text
State/<Instance>/<Scope>/RohTalk/Workflow/Conversations/
```

Important skills include:

```bash
python nspl.py skill RohTalk.start -- "Hello"
python nspl.py skill RohTalk.start --tools -- "Use tools if needed"
python nspl.py skill RohTalk.chat 0 -- "Continue"
python nspl.py skill RohTalk.list_conversations
python nspl.py skill RohTalk.show_conversation 0
python nspl.py skill RohTalk.oneshot -- "Quick prompt"
python nspl.py skill RohTalk.tool_test -- "Test tools"
python nspl.py skill RohTalk.shell --conversation 0 --tools --toolkit basic
python nspl.py skill RohTalk.shell --conversation 0 --watch
```

RohTalk is intended to be the AI/operator substrate for apps such as LifeRPG and DST, not just a chat wrapper. Persistent conversations, shell/watch mode, and note injection are strategically important for multi-agent workflows because they let humans, CLI agents, and future Web surfaces share one durable conversation artifact.

Do not overstate maturity:

- RohTalk has no dedicated Web UI yet.
- Long conversation summarization/maintenance is not automatic yet.
- App-specific context layering is still a design/integration task.
- Toolkits exist, but should remain safe semantic surfaces rather than raw command exposure.

## LLMClient

`Core/LLMClient` provides model backend access, currently focused on Ollama-style chat/generate/streaming behavior.

LLMClient should remain backend-facing and reusable. App/product code should not hardcode HTTP model details when LLMClient already provides a seam.

## LifeRPG

LifeRPG.App is the gamified life command center.

Elevator pitch:

> LifeRPG is your command center for turning your messy day into playable missions.

Vocabulary:

- Mission = the day/current operation
- Quest = actionable task
- Event = scheduled/calendar item
- Habit = recurring upkeep
- Build = category for coding/creative/client/project work
- Roh = Operator
- Agents/Echoes/Signal/Signal Gate = future game/lore layer

Current implemented layers:

```text
Core/LifeRPG/          models, store, services, deterministic sorting, rewards, sessions, expedition
Skills/LifeRPG/        thin skill wrappers for inbox, quests, habits, events, settings, mission, expedition
Web/LifeRPG/App/       FastAPI/Jinja/HTMX browser app
Docs/Plans/LifeRPG/    design doc, mockups, art manifest
```

Current state default:

```text
State/main/Global/LifeRPG/...
```

Implemented concepts:

- quick dump / inbox capture
- deterministic template Roh sorting
- inbox edit/archive/revert
- quests, quest sessions/time cards, pause/complete notes
- default habits and habit management
- event management with reminder fields
- settings/profile persistence
- reward ledger with XP and Leisure Tokens
- simple session-tied expedition simulation with dynamic allies/enemies
- compact command-center Board after UX rescue

Important UX contract:

- Board is not a CRUD wall.
- Use compact previews and progressive disclosure.
- Use selects for enum-style fields.
- Settings shown in UI should have real visible/behavioral effect.
- HTMX actions should update affected panels coherently.

Deferred:

- live RohTalk integration
- ClickUp provider
- browser notifications
- auth/multi-user accounts
- node targeting/conflict strategy
- real combat/gameplay
- Signal Gate/gacha
- Dice/Alea combat
- full calendar widget
- speech-to-text
- production hosting/security

## DST / RohBridge

`Core/Game/DST` owns reusable RohBridge contracts:

- path discovery
- command validation
- command queue JSON
- legacy command writes
- result polling

DST skills are thin wrappers around these Core contracts.

RohBridge paths include:

- `snapshot_path`
- `command_path`
- `command_queue_path`
- `command_result_path`
- `save_dir`
- `source`

Queued command writes use `roh_dst_command_queue.json` and schema `dst.v0.4.command_queue`. Result polling reads `roh_dst_command_result.json` and matches by `command_id`.

The `dst_director` RohTalk toolkit exposes model-facing tools for safe DST actions such as snapshot reads, announcements, objectives, chaos tier changes, allowlisted supply/enemy spawns, frog-rain events, and tracked spawn cleanup.

Do not expose raw low-level DST command writers to model toolkits by default.

## AutoRoh

AutoRoh is a generic observed, tool-capable loop. It is not DST-specific.

Core module boundaries:

- `state.py`: durable loop state
- `notes.py`: human note scanning
- `observations.py`: observation tool execution and signature hashing
- `tool_events.py`: tool call/result event shaping and action signatures
- `policy.py`: advisory cooldown text
- `prompts.py`: tick prompt construction
- `profiles.py`: toolkit/workflow-specific behavior, rules, cooldowns
- `director_packs.py`: generic domain content pack loading/rendering

`Skills/AutoRoh/run` is the orchestration entrypoint. It should delegate reusable behavior to Core modules.

New workflows should add profiles/toolkits instead of hardcoding workflow behavior into AutoRoh.

## ChatOps

ChatOps is a filesystem-native task queue built on NodeCTX and SkillCLI concepts.

Design:

- tasks are files
- state transitions are folder moves
- results are JSON
- filesystem is truth
- no hidden queues/databases

ChatOps is infrastructure. It should not depend on RohTalk, CLM, or a specific app.

## Video / LookLab

`Core/Video` provides reusable FFmpeg/video/frame processing:

- frame discovery and ping-pong sequencing
- frames-to-video preparation/execution
- video export and filter composition
- fit/crop/pad logic
- ffprobe duration probing
- FFmpeg execution helpers

`GUI/Video/LookLab` is the first working GUI vertical slice.

LookLab currently uses a GUI -> Core model. Long-term target is tighter alignment with Video Skills or thinner GUI behavior that mirrors Skill behavior.

LookLab matters because it proves:

- Entry GUI discovery
- launcher flow
- dependency verification
- FFmpeg integration
- progress parsing through Proc
- usable video workflow chaining

## Web Apps

`Web/NSPL/Status` is the reference Web app proving Entry/Web/Skill loop.

`Web/LifeRPG/App` is the first major product-shaped Web app.

Web apps should follow:

- FastAPI/Jinja/HTMX for now
- no frontend build tooling unless explicitly approved
- `create_app(context)` factory
- Entry-owned launch
- state mutations through Skills/Core
- progressive disclosure for management UI
- no raw CRUD walls on command-center boards

## Future Hosting Direction

NSPL Web apps can technically run on any server with Python and dependencies installed, but public hosting is not safe yet.

Local/private phases:

1. localhost only
2. Tailscale/private LAN
3. private/staging server
4. public web only after auth/permissions/security work

Public/server-hosted NSPL will need:

- authentication/login
- user/profile separation
- skill allowlists/permissions
- CSRF protection
- environment/config management
- service management
- backup/restore
- audit logs
- reverse proxy and HTTPS docs

Until then, do not expose full NSPL command surfaces publicly.
