# NSPL Agent Docs

This folder contains source context docs for coding agents, reviewer agents, and humans working in NSPLDev.

## Source Docs

Read in this order when broad context is needed:

1. `00_NSPL_AGENT_BRIEF.md` - first-context brief and repo rules
2. `01_NSPL_ARCHITECTURE_AND_COMMANDS.md` - architecture and command surfaces
3. `02_PROJECT_CONTEXTS.md` - current project/domain status
4. `03_AGENT_WORKFLOW_AND_STATUS.md` - pass workflow and status
5. `04_NSPL_VISION_AND_ROADMAP.md` - platform vision and roadmap
6. `05_NSPL_PROTOCOLS_AND_DESIGN_RULES.md` - architecture and safety protocols
7. `06_NSPL_WEB_APP_UX_CONTRACT.md` - Web UX contract
8. `07_NSPL_RELEASE_AND_PUBLIC_DEMO_STRATEGY.md` - release/demo strategy

These docs supplement `AGENTS.md`, `00_AGENT_HANDOFF.md`, project README files, and design docs under `Docs/Plans/`.

## Recommended Read Paths

Focused coding pass:
`00`, `01`, `02`, `03`, plus relevant project README/design docs.

Architecture review:
`00`, `01`, `02`, `04`, `05`, and `KNOWN_ISSUES.md`.

Web UX/product pass:
`00`, `01`, `02`, `03`, `05`, `06`, plus the target app README/design docs.

Public/demo/release pass:
`00`, `01`, `02`, `04`, `05`, `07`, `Docs/README.md`, and `KNOWN_ISSUES.md`.

LifeRPG pass:
`00`, `01`, `02`, `03`, `06`, `Docs/Plans/LifeRPG/LifeRPG-App-MVP-Design.md`, `Core/LifeRPG/README.md`, `Web/LifeRPG/App/README.md`, and relevant tests.

RohTalk pass:
`00`, `01`, `02`, `03`, `05`, `Core/RohTalk/README.md`, `Skills/RohTalk/README.md`, and relevant tests.

## Bundles

Generated bundles under `Docs/Bundles/` are derived from source docs. Edit source docs first, then regenerate bundles only when a pass explicitly requires it.
