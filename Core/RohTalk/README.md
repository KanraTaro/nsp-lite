# RohTalk Core

RohTalk is a persistent, tool-capable conversation runtime built on NSP Lite.

It provides a filesystem-backed agent loop that supports:

- multi-turn conversations
- durable message history
- tool execution with iterative reasoning
- backend-agnostic message normalization
- CLI-driven interaction via SkillCLI

This is no longer a single-turn chat wrapper.  
RohTalk is now a local agent runtime with memory and tools.

---

## Core Capabilities

### Persistent Conversations

Each conversation is stored on disk via NodeCTX and can be:

- created
- resumed
- appended to
- inspected

All state lives under:

State/<Instance>/<Scope>/RohTalk/Workflow/Conversations/

Each conversation includes:

- full normalized message history (in metadata JSON)
- append-only event log (JSONL)

---

### Tool-Capable Reasoning Loop

RohTalk supports multi-step tool usage within a single turn.

Flow:

1. user message added to history
2. model runs via chat_stream_collect(...)
3. assistant message appended
4. if tool calls are present:
   - tools executed via tool_runner
   - tool results appended
   - loop continues
5. final assistant response returned

This enables:

- iterative reasoning
- tool grounding
- multi-step decision making

---

### Normalized Message Format

All messages are stored in a backend-agnostic structure:

Assistant tool call:

{
  "role": "assistant",
  "content": "",
  "tool_calls": [
    {
      "id": "...",
      "name": "...",
      "arguments": {...}
    }
  ]
}

Tool result:

{
  "role": "tool",
  "tool_call_id": "...",
  "tool_name": "...",
  "content": "{...json...}"
}

This ensures:

- provider independence (Ollama, OpenAI, etc.)
- replayable conversations
- inspectable history
- stable internal contracts

---

### Streaming Support

RohTalk is built on LLMClient streaming:

- text is streamed during generation
- tool calls are detected during streaming
- final assistant message is normalized and stored

Streaming is optional at the caller level, but supported end-to-end.

---

### CLI Usage

RohTalk is accessed through SkillCLI.

Examples:

# Start a conversation
python nspl.py skill RohTalk.start -- "Hello"

# Start with tools enabled
python nspl.py skill RohTalk.start --tools -- "What's the weather in Orlando?"

# Continue a conversation
python nspl.py skill RohTalk.chat 0 -- "How are you?"

# Continue with tools
python nspl.py skill RohTalk.chat --tools 0 -- "What's the weather in New York?"

# Inspect conversation
python nspl.py skill RohTalk.show_conversation 0

---

## Architecture

Directory layout:

Core/RohTalk/
  __init__.py
  config.py
  messages.py
  conversations.py
  runner.py
  tool_loop.py
  tool_runner.py
  Tests/

---

### Responsibilities

config.py
Loads and merges configuration values

messages.py
Builds system + user message payloads

conversations.py
Handles durable storage, retrieval, and updates

runner.py
Single-turn orchestration (non-tool mode)

orchestrator.py
Shared `run_turn` seam for plain and tool-capable turns

tool_loop.py
Multi-step tool-capable reasoning loop

tool_runner.py
Execution seam for tool calls

skillcli_tools.py
SkillCLI bridge for model-facing tools

toolkits.py
Named model-facing toolkits

tracing.py
Optional console tracing callbacks

---

## Storage Model

Each conversation is stored as:

<conversation_id>.json
<conversation_id>.events.jsonl

Metadata includes:

- id
- created_at
- updated_at
- messages (full normalized history)
- model
- agent identity
- kind (conversation / oneshot)

Event logs provide append-only auditing and replay.

---

## Configuration

Configuration is loaded from:

1. State/<Instance>/<Scope>/RohTalk/Config/config.json
2. Config/RohTalk/config.json

Supported keys:

- agent_name
- agent_identity
- default_model
- default_host
- default_options
- profiles

Missing values fall back to defaults.

`default_options` is a JSON object merged into model requests. For Ollama,
these keys are sent as top-level request fields, so live-agent settings such as
`"think": false` or `"think": "low"` are API controls rather than prompt text.

`profiles` is a map of named runtime presets. A profile can define `model`,
`host`, and `options`; explicit CLI `--model`, `--host`, and `--model-option`
values override profile values.

Example:

```json
{
  "default_model": "gpt-oss:20b",
  "default_options": {
    "think": "low"
  },
  "profiles": {
    "dst_director_fast": {
      "model": "qwen3:8b",
      "options": {
        "think": false
      }
    }
  }
}
```

---

## Design Principles

### Filesystem is Truth

All state is persisted via NodeCTX:

- no hidden memory
- no in-process state reliance
- everything observable on disk

---

### Backend Agnostic

RohTalk does not depend on provider-specific formats.

LLMClient handles translation.  
RohTalk only consumes normalized messages.

---

### Tool Execution is Abstracted

RohTalk can execute model-requested tools through SkillCLI-backed skills.
Named toolkits expose model-facing tool definitions and map those names back
to canonical SkillCLI skill names. Local in-process callables remain available
as a bootstrap/testing backend.

This gives one execution surface for:

- humans using SkillCLI
- agents using RohTalk tool loops
- automation such as AutoRoh

---

### Streaming + Determinism

- streaming provides real-time feedback
- final stored state is always normalized and deterministic

---

## What It Does NOT Do (Yet)

- no persona system (beyond config identity)
- no dynamic tool registry or capability profiles
- no automatic context compression
- no ChatOps orchestration
- no dedicated Web UI yet
- no automatic long-conversation compaction yet
- app-specific context layering is still integration work

---

## Current Status

RohTalk currently supports:

- persistent conversations
- tool usage within conversations
- multi-step reasoning loops
- normalized, inspectable history
- CLI-based interaction
- interactive `RohTalk.shell`, read-only watch mode, and `/note` injection

This is the foundation for:

- AutoRoh
- tool-driven agents
- distributed NSP workflows

---

## See Also

Skills/RohTalk/README.md  
Core/NSPL/NodeCTX/README.md  
Core/LLMClient/README.md
