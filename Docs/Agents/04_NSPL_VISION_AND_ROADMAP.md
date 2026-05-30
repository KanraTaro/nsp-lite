# NSPL Vision and Roadmap

## Working Definition

NSPL is a local-first, filesystem-backed AI operating layer for building apps, agents, games, automations, creator tools, business workflows, and trusted multi-node collaboration systems.

It is not a single app. It is not only a chatbot wrapper. It is not only a task runner.

NSPL is a repeatable architecture for turning human intent into inspectable, durable, agent-usable systems.

Short version:

> NSPL lets humans and AI agents build, operate, and coordinate real software through explicit files, thin command surfaces, Web/GUI control panels, and durable state.

Deeper version:

> NSPL is a local-first runtime and development pattern where apps, tools, state, plans, logs, tests, reports, and AI context all become visible artifacts that humans and their AI collaborators can inspect, reuse, and continue.

## Why NSPL Exists

Most AI workflows are trapped inside chat windows, SaaS platforms, browser tabs, provider-specific integrations, and hidden memories. They can be useful, but they are fragile.

Common problems:

- the AI forgets too much between sessions
- context is hidden inside conversations instead of saved as artifacts
- tool behavior is opaque
- app state lives in services the user does not control
- automations are hard to inspect
- workflows are tied to one provider
- local machines and home servers are underused
- different projects cannot share the same durable state model
- AI-assisted development often leaves no clean trail for other agents or humans to follow

NSPL exists to make these things explicit.

The filesystem is the shared memory layer. Skills are the action layer. Web and GUI apps are control surfaces. RohTalk is the AI conversation and tool runtime. NodeCTX defines where durable state belongs. Plans, reports, tests, and docs become part of the development process.

## Core Belief

A useful AI system should not be a black box.

It should leave traces. It should be inspectable. It should be recoverable. It should be portable. It should be able to degrade gracefully. It should let humans stay in control while giving AI agents enough structure to act.

NSPL is built around that belief.

## The NSPL Loop

Most NSPL systems follow this loop:

1. Human intent enters the system.
2. Context is loaded from files, docs, app state, or conversation history.
3. An AI agent or human chooses an action.
4. The action runs through a Skill, Core service, Web route, GUI action, or queue.
5. State is written to disk through NodeCTX.
6. Logs and reports record what happened.
7. Web/GUI surfaces update.
8. Reflection or review turns results into future context.
9. The next pass becomes easier.

Shorthand:

> Intent → Context → Action → Filesystem State → Feedback → Reflection → Better Context

This loop applies to LifeRPG, RohTalk, DST, video tools, business automation, and future NSPL apps.

## Strategic Pillars

### 1. Local-First Control

NSPL should work on a user’s own machine or trusted server before depending on cloud services. Local-first does not mean isolated forever. It means the user’s system has durable local truth first, and cloud/network integrations become optional providers rather than the source of identity.

### 2. Filesystem Truth

The filesystem is not just storage. It is the observable state layer.

Important state should be visible in files:

- tasks
- conversations
- app settings
- command queues
- event logs
- active sessions
- generated reports
- reflections
- agent handoffs
- plans
- context bundles

This is what makes NSPL inspectable by humans, agents, sync tools, backup systems, and future GUIs.

### 3. Thin Action Surfaces

Skills are thin, executable action surfaces. They parse arguments, call Core logic, print output, and return exit codes. They should be accessible to humans, Web apps, GUI apps, RohTalk, AutoRoh, ChatOps, and future model-facing toolkits.

### 4. Reusable Core Logic

Core modules own reusable behavior. A good NSPL app has Core domain logic, Skills exposing actions, Web/GUI surfaces for users, NodeCTX-backed state, tests proving behavior, and docs explaining the contract.

### 5. Agent-Usable Development Artifacts

NSPL is being developed so the development process itself becomes usable by AI agents.

Every serious pass should produce artifacts:

- design docs
- tests
- implementation reports
- known issues
- generated context bundles
- updated status docs
- human review notes
- screenshots/mockups when useful

The goal is that a developer can bring their own AI agent to the repo and say:

> Read the agent bundle, read the project plan, inspect the current diff, and help me continue.

That is not side documentation. That is part of the platform.

### 6. Web Apps as Command Surfaces

NSPL Web apps are local-first browser/mobile interfaces for the underlying Core/Skill/state system. They should feel like real apps, not raw admin panels.

A good Web app guides the user, hides complexity until needed, uses progressive disclosure, updates related panels coherently, uses durable state instead of browser-only truth, and exposes the right actions without exposing unsafe internals.

### 7. AI Operators, Not Stateless Chatbots

RohTalk is the path toward persistent AI operators.

An NSPL agent should eventually be able to understand the user’s current app context, inspect app state, call tools safely, propose changes, execute approved actions, reflect on outcomes, maintain continuity across sessions, and communicate with other trusted agents.

LifeRPG, DST, Video, and future apps should be able to use RohTalk rather than each inventing a separate AI brain.

### 8. Trusted Multi-Node Collaboration

Long-term, NSPL should support trusted users and trusted nodes:

- personal machines
- home servers
- trusted personal devices
- friend/collaborator nodes
- business partner systems
- local or private hosted servers

Agents may eventually coordinate across trusted nodes. People may share compute, storage, automation, app access, or project state with people they trust. This is not public cloud first. It is trust-network first.

## Current Strategic Demos

### LifeRPG

LifeRPG is the personal command center demo. It turns messy life tasks into missions, quests, habits, events, sessions, rewards, and game loops.

Why it matters:

- proves Web app pattern
- proves app state through NodeCTX
- proves Core/Skills/Web layering
- proves AI/operator design path
- proves gamified productivity as a real app
- gives normal users something understandable

### RohTalk

RohTalk is the AI operator runtime.

Why it matters:

- persistent conversations
- tool-capable loops
- model backend abstraction
- Skill access
- app-specific context layering
- future Roh Station / Operator interfaces

RohTalk is strategically central because every AI-powered NSPL app should eventually be able to use it.

### DST / RohBridge

DST/RohBridge is the game-agent proof.

Why it matters:

- proves NSPL can observe and act in external systems
- uses snapshots, command queues, and result polling
- demonstrates model-facing tool safety
- connects Roh to a real game loop
- gives a visually interesting demo path

### Video / LookLab

Video/LookLab is the creator tooling proof.

Why it matters:

- proves GUI launch paths
- proves FFmpeg/process integration
- supports real creator workflows
- shows NSPL is not only AI chat or productivity
- can connect to creator and project workflows

### Web/NSPL/Status

Status is the reference Web app. It proves Entry/Web launch and Skill invocation from WebContext.

## Use Case Horizon

NSPL should be able to grow into many domains without changing its core philosophy:

- personal life management
- personal and home systems
- business and client work
- creative tooling
- games and simulations
- coding and development
- security and operations
- trusted local-cloud collaboration

## Roadmap Stages

### Stage 0: Local Foundation

Prove that NSPL can run useful local apps, Skills, and Web/GUI surfaces.

### Stage 1: App Creation Discipline

Make it easy to create consistent NSPL apps with stronger templates, UX contracts, generated agent docs, common UI patterns, asset manifests, reusable Web helpers, and test patterns.

### Stage 2: RohTalk Integration

Make Roh the operator layer across apps: RohTalk Web UI, app-specific context builders, structured action proposals, safe multi-tool execution, conversation summarization, LifeRPG Roh Station, DST director improvements.

### Stage 3: Friendly User Testing

Let trusted testers run instances through cleaner install/update flows, per-user instance patterns, simple launch scripts, safer state defaults, and backup/reset helpers.

### Stage 4: Developer Preview

Make the repo understandable and testable by external developers: public README cleanup, agent context bundles, contributor docs, installation docs, sample apps, passing tests, screenshots/demos, and honest limitations.

### Stage 5: Private Hosted Mode

Run NSPL Web apps on trusted servers with service management, reverse proxy docs, Tailscale/private access docs, basic auth/session layers, CSRF protection, skill permission allowlists, backup/restore, and deployment profiles.

### Stage 6: Trusted Multi-Node Network

Connect trusted user nodes and agents through node identity, state sync strategy, conflict handling, permissions, agent-to-agent messaging, trusted resource sharing, and audit logs.

### Stage 7: Public Platform Layer

Make NSPL a serious local-first AI app platform with stable contracts, versioning, app templates, security hardening, public docs, community examples, contributor workflow, and optional hosted/private deployments.

## What NSPL Is Not

NSPL is not trying to be a cloud SaaS clone. It is not trying to hide everything behind a database. It is not trying to make humans irrelevant. It is not trying to force every app into one UI. It is not trying to make AI agents act without boundaries. It is not finished yet.

It is a growing local-first operating layer for building systems that humans and AI agents can understand together.

## Public Positioning Draft

NSPL is a local-first architecture for building AI-assisted apps, tools, and agents where the filesystem stays readable, actions run through explicit Skills, and development leaves artifacts that both humans and AI collaborators can follow.

Instead of hiding state in cloud services or one-off chat sessions, NSPL makes apps, workflows, logs, tests, plans, and agent handoffs visible in the repo.

It is currently being proven through LifeRPG, RohTalk, DST/RohBridge, and creator/video tooling.

The goal is to let people build useful local AI systems that can later grow into trusted networks of personal agents, home servers, collaborators, and private tools.
