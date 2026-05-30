# NSPL Documentation Index

This directory contains source docs, project plans, generated bundle manifests, reports, and known issues for NSPLDev.

## Main Areas

- `Agents/`: source context docs for coding agents, reviewer agents, and humans.
- `Developer/`: practical contributor guides for Skills, Web apps, NodeCTX state, RohTalk integration, validation, and pass reports.
- `Plans/`: project and product plans. These are source docs unless a file clearly says it is generated.
- `Bundles/`: generated-context bundle manifest and bundle docs. Edit source docs first.
- `Reports/`: pass reports from Codex, Claude, and human reviews.
- `KNOWN_ISSUES.md`: active platform limitations and hardening work.

## Source Docs

Source docs are the files humans should edit:

- `Docs/Agents/*.md`
- `Docs/Developer/*.md`
- `Docs/Plans/**/*.md`
- `Docs/KNOWN_ISSUES.md`
- project README files under `Core/`, `Skills/`, `Web/`, and `GUI/`

## Generated Bundles

Bundles are generated from source docs using `Docs/Bundles/bundles.json`. Do not hand-edit generated bundle outputs except to delete stale outputs during cleanup.

Current bundle definitions:

- `nspl-full`
- `nspl-public`
- `liferpg`
- `rohtalk`

## Recommended Reading

Focused coding:
`AGENTS.md`, `00_AGENT_HANDOFF.md`, `Docs/Agents/00` through `03`, and touched project README files.

Architecture review:
`Docs/Agents/00`, `01`, `02`, `04`, `05`, and `KNOWN_ISSUES.md`.

Web UX/product:
`Docs/Agents/06`, `Docs/Developer/Web-App-UX-Patterns.md`, and the target app design docs.

RohTalk:
`Docs/Agents/02`, `Docs/Developer/RohTalk-Integration-Guide.md`, `Core/RohTalk/README.md`, and `Skills/RohTalk/README.md`.

LifeRPG:
`Docs/Agents/02`, `Docs/Agents/06`, `Docs/Plans/LifeRPG/LifeRPG-App-MVP-Design.md`, `Core/LifeRPG/README.md`, and `Web/LifeRPG/App/README.md`.
