# NSPL Release and Public Demo Strategy

## Purpose

This document defines how NSPL should move from private development to demos, trusted testing, developer previews, and eventual public sharing.

NSPL is powerful because it can run local apps, expose Web surfaces, call Skills, manage filesystem state, and connect AI agents to real actions.

That also means public exposure must be handled carefully.

## Current Public Positioning

NSPL is a local-first architecture for building AI-assisted apps, agents, tools, games, and automations where:

- filesystem state remains visible
- actions run through explicit Skills
- Core logic is reusable and testable
- Web/GUI apps are control surfaces
- AI context is preserved in docs and reports
- humans and AI agents can develop together through artifacts

Short public line:

> NSPL is a local-first AI app platform where the filesystem is truth, Skills are actions, Web/GUI apps are control surfaces, and development leaves artifacts that humans and AI agents can both follow.

## Why This Matters

Most people using AI are connecting cloud chatbots to cloud services like ClickUp, WordPress, MailerLite, Google Calendar, social platforms, CRMs, and web apps.

That can be immediately useful.

The downside is that the workflow usually lives across many external services. The memory, logic, and state may be spread across tools the user does not fully control.

NSPL explores another path:

- local-first
- inspectable
- user-owned
- portable
- extensible
- agent-friendly
- multi-node ready
- suitable for personal, creator, team, and game workflows

The point is not that existing web-app integrations are bad. The point is that NSPL builds a durable foundation that can eventually power many workflows without locking the user into one provider’s interface or memory model.

## Demo Stages

### Stage 0: Local Developer Demo

Audience: core maintainers, close collaborators, AI agents, technical reviewers.

Access: localhost only.

Examples:

```bash
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
python nspl.py skill RohTalk.start -- "Hello"
```

Safe because there is no public exposure, local files only, and the human controls the machine.

### Stage 1: Trusted Household / Friend Testing

Audience: trusted testers and close collaborators.

Access: local machine, separate NSPL instance, private LAN, Tailscale, manually configured ports.

Requirements:

- clearer launch docs
- stable app commands
- state reset/backup guidance
- basic safety notes
- separate instance patterns

### Stage 2: Private Server Staging

Audience: trusted users, team staging, local server, private deployments.

Access: Python-capable server, LAN or Tailscale preferred, reverse proxy optional, no public unrestricted Skill access.

Requirements:

- service management
- environment/dependency docs
- backup/restore docs
- state ownership patterns
- basic auth/session if exposed beyond trusted network
- safe app allowlist

### Stage 3: Developer Preview

Audience: external developers, Reddit technical readers, open-source contributors, AI-assisted dev experimenters.

Access: public repo, local install, clear demo commands, known issues stated.

Requirements:

- clean README
- install guide
- agent context bundles
- screenshots
- sample workflows
- tests passing
- docs explaining architecture
- warning about local-first/development status
- no secrets or personal State

### Stage 4: Public Web Exposure

Audience: broader users, hosted deployments, client-facing systems.

Access: public internet.

Do not enter this stage until NSPL has authentication/login, user/profile separation, CSRF protection, skill allowlists/permissions, reverse proxy/HTTPS docs, service deployment docs, state backup/restore, audit logs, public/private app boundary, safe defaults for network binding, and a threat model for Web-to-Skill execution.

## What Is Demoable Now

### LifeRPG.App

Demo value:

- shows NSPL Web apps
- shows LifeRPG command center
- shows NodeCTX-backed state
- shows Skills + Core + Web layering
- shows gamified productivity direction
- shows AI operator path even before full RohTalk integration

Current limitations:

- expedition simulation is shallow
- rewards are placeholder-level
- RohTalk is not wired in yet
- visuals are not final
- not ready for public user data
- not public-hosting safe

### Web/NSPL/Status

Demo value:

- minimal reference Web app
- proves Entry/Web/Skill loop

### RohTalk

Demo value:

- persistent conversation runtime
- Skill/tool-capable direction
- key to Roh as operator

Current limitations:

- needs Web UI
- needs better long conversation maintenance
- app-specific context layers still evolving

### DST / RohBridge

Demo value:

- visually interesting game-agent proof
- shows AI can observe and act in a game loop
- demonstrates safe tool abstraction over raw commands

Current limitations:

- still development/demo oriented
- not a general game framework yet
- needs better UI/status surfaces

### Video / LookLab

Demo value:

- creator tooling proof
- FFmpeg integration
- GUI proof
- useful for creator and project workflows

## What Is Not Public-Safe Yet

Do not publicly expose:

- unrestricted Skill execution
- Web apps that can call arbitrary local actions
- personal State data
- RohTalk conversations with private context
- unprotected hosted NSPL servers
- node control surfaces without auth
- local filesystem tools without allowlists
- provider credentials or tokens
- private personal or client data

## Contributor Story

NSPL should be developed in a way that contributors can bring their own AI agents.

A new contributor should be able to:

1. clone or download the repo
2. read source docs listed in `Docs/Agents/README.md` or a generated bundle defined in `Docs/Bundles/bundles.json`
3. run tests
4. launch a demo app
5. read project-specific plans
6. ask their AI agent to review or implement a scoped pass
7. save the agent’s report under `Docs/Reports/`
8. submit a clean change with tests and docs

This is part of the platform identity.

NSPL is not just AI-assisted code.

NSPL is artifact-assisted AI development.

## AI Agent Context Bundles

Context bundles should exist for different audiences:

### Agent Quick Context

For focused Codex/Claude tasks. Contains the minimum repo rules, command references, project context, and current status.

### Agent Full Context

For larger architecture review. Contains vision, protocols, UX contract, release strategy, known issues, and project contexts.

### Developer Context

For contributors. Contains how to create Skills/Web apps, NodeCTX state rules, testing and validation.

### LifeRPG Context

For LifeRPG-specific work. Contains NSPL basics, Web UX contract, LifeRPG MVP design, current status.

### Public Overview

For nontechnical or semi-technical explanation. Contains vision, demos, roadmap, and why the platform matters.

## Business Explanation Angle

For business-minded readers, NSPL should be explained honestly.

Short-term, connecting Claude to existing web apps can produce faster immediate automation value.

NSPL is different. It is an owned foundation.

It is valuable because it can become:

- a private automation layer
- a local app platform
- a personal/team control system
- a reusable workflow engine
- an AI operator runtime
- a way to avoid being locked into one provider’s memory/integration model
- a system that can grow from personal tools to business automations and trusted collaboration

The business explanation:

> Existing AI integrations help automate today’s tools. NSPL is about owning the layer underneath those automations so workflows, context, state, and agents remain portable, inspectable, and extensible over time.

## Reddit / Public Post Angle

Potential public framing:

> I’m building NSPL, a local-first AI app/runtime architecture where the filesystem is truth, Skills are actions, Web apps are command surfaces, and every development pass leaves artifacts that both humans and AI agents can follow.
>
> The current demos include LifeRPG, a gamified daily command center; RohTalk, a persistent local AI/operator runtime; a Don’t Starve Together game-agent bridge; and creator/video tooling.
>
> The goal is not just one app. The goal is a pattern for building local AI systems that can grow into trusted networks of personal agents, home servers, collaborators, and private tools.

## Release Readiness Checklist

Before public developer preview:

- README explains NSPL clearly
- install instructions work
- tests pass
- State is excluded
- screenshots are included
- LifeRPG demo launches
- RohTalk demo works
- Status Web demo works
- known issues are honest
- context bundles exist
- no personal/private state in repo
- security limitations are stated
- contribution workflow is explained

Before hosted/public deployment:

- auth
- permissions
- CSRF
- HTTPS/reverse proxy docs
- service setup
- backup/restore
- logging/audit
- skill allowlist
- user/profile isolation
- state conflict strategy
- public/private boundary

## Suggested Public Demo Order

1. Show NSPL Status app as platform proof.
2. Show LifeRPG as user-facing Web app.
3. Show RohTalk as persistent operator runtime.
4. Show DST/RohBridge as game-agent proof.
5. Show Video/LookLab as creator tooling proof.
6. Explain the shared architecture underneath.
7. Explain agent context bundles and artifact-driven development.

## Summary

The safe release strategy is:

> Demo locally, test with trusted people, document aggressively, expose only what is safe, and make every development artifact useful to both humans and AI agents.

The public message is:

> NSPL is a local-first AI app/runtime platform for people who want useful AI systems they can own, inspect, extend, and develop alongside their own agents.
