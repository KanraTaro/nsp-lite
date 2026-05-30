# RohTalk Integration Guide

RohTalk is the shared NSPL operator runtime. Apps should treat it as the substrate for AI-assisted conversations and tool use instead of inventing separate app-specific AI brains.

## Current Components

From the current implementation:

- `Core/RohTalk/conversations.py`: persistent conversation metadata and event logs through NodeCTX.
- `Core/RohTalk/messages.py`: normalized message assembly helpers.
- `Core/RohTalk/runner.py`: plain conversation turn orchestration.
- `Core/RohTalk/orchestrator.py`: `run_turn` seam that selects plain or tool-capable turns.
- `Core/RohTalk/tool_loop.py`: iterative streamed model/tool loop.
- `Core/RohTalk/tool_runner.py`: normalized tool execution result handling.
- `Core/RohTalk/skillcli_tools.py`: SkillCLI bridge for model-facing tools.
- `Core/RohTalk/toolkits.py`: named toolkits such as `basic` and `dst_director`.
- `Core/RohTalk/tracing.py`: console tracing callbacks.
- `Skills/RohTalk/*`: CLI entrypoints including `RohTalk.shell`.

## App Context Layering

Apps should assemble context in layers:

1. RohTalk identity/config.
2. User or instance profile.
3. App profile/preferences.
4. Current app state summary.
5. Recent app events/logs.
6. Available safe app actions.
7. User request.

The app should not send raw state dumps when a compact summary is enough.

## Tool Design

Expose semantic app actions through Skills and toolkits. Avoid raw file writers, shell tools, or internal debug commands as model-facing tools.

Good:

- `LifeRPG.Inbox.Sort`
- `LifeRPG.Quest.Start`
- `Game.DST.Objective.status`

Risky:

- unrestricted file write
- raw command queue writer
- arbitrary shell

## LifeRPG Seam

LifeRPG should eventually use RohTalk for Operator behavior:

- inbox sorting with app context
- quest breakdown
- next-action proposals
- recovery/check-in guidance
- structured action proposals and execution summaries

This is a future/high-priority integration seam. Current LifeRPG sorting remains deterministic/template-based unless a pass explicitly wires RohTalk in.

## Multi-Agent Workflows

Persistent conversations, `RohTalk.shell`, watch mode, and `/note` injection matter because they let humans, agents, and future Web surfaces coordinate through one durable conversation artifact.

Known gaps:

- no dedicated RohTalk Web UI yet
- no automatic long conversation compaction yet
- app-specific context builders are still needed
