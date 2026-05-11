# LLMClient Core

LLMClient is a backend-agnostic interface for interacting with language models.

It provides a normalized contract for:

- chat completion
- streaming responses
- tool call extraction
- assistant message normalization

LLMClient is the translation layer between external model providers and NSP systems like RohTalk.

---

## Core Responsibilities

### Unified Chat Interface

LLMClient exposes a consistent API across providers:

- Ollama (current)
- OpenAI (future)
- other backends (planned)

All providers are normalized into the same internal structures.

---

### Normalized Output

Every chat call returns a `ChatResult`:

- `text` — final assistant text
- `tool_calls` — structured tool requests
- `assistant_message` — normalized message ready for history
- `raw` — provider response for debugging

This allows higher-level systems to operate without caring about provider format.

---

### Streaming Support

LLMClient supports streaming via:

`chat_stream(...)`

which yields incremental `StreamEvent` objects:

- text deltas
- tool call detection
- raw provider chunks

It also supports:

`chat_stream_collect(...)`

which:

- consumes the stream
- reconstructs the final response
- returns a normalized `ChatResult`

This enables both:

- real-time UX
- deterministic stored state

---

### Tool Call Normalization

Providers return tool calls in different shapes.

LLMClient normalizes them into `ToolCall` objects with:

- `id`
- `name`
- `arguments`
- `arguments_json`

Key guarantee:

- `tool_call_id` is always stable and present

If the backend does not provide an ID, LLMClient generates one.

This ensures tool execution and tool result mapping always works.

---

### Message Normalization

LLMClient converts between:

- internal normalized messages
- provider-specific payloads

Normalized assistant tool-call message:

{
  "role": "assistant",
  "content": "",
  "tool_calls": [
    {
      "id": "...",
      "name": "...",
      "arguments": { ... }
    }
  ]
}

Normalized tool result message:

{
  "role": "tool",
  "tool_call_id": "...",
  "tool_name": "...",
  "content": "{...json...}"
}

This allows higher-level systems to persist and replay model interactions without storing provider-specific formats.

---

## Architecture

Core/LLMClient/
  client.py
  types.py
  http_json.py
  http_stream.py
  backends/
    ollama.py
  Tests/

---

### Module Responsibilities

`client.py`
- public interface
- backend dispatch
- streaming collection
- normalized result construction

`types.py`
- shared structures
- error definitions
- dependency injection protocols

`http_json.py`
- HTTP JSON helper functions
- non-streaming request support

`http_stream.py`
- streaming HTTP helpers
- NDJSON/event-style response handling

`backends/ollama.py`
- Ollama-specific request formatting
- streaming parse logic
- tool call extraction
- assistant message normalization
- top-level model runtime options such as `think`

---

## Design Principles

### Backend Agnostic

LLMClient hides provider differences completely.

Callers should never depend on:

- raw provider message formats
- streaming response shapes
- provider-specific tool schemas

---

### Streaming First, Deterministic Final

- streaming gives the caller real-time visibility
- final results are always normalized into stable structures

This keeps UX responsive while preserving clean persistence behavior.

---

### Stable Tool Contracts

Tool calls are normalized and ID-stable across providers.

This is critical for:

- multi-step tool loops
- replaying conversations
- switching providers without breaking behavior

---

### Minimal Surface Area

LLMClient does not:

- manage conversations
- store persistent state
- execute tools
- run agent loops

It only:

- talks to language model backends
- normalizes results into NSP-friendly structures

---

## What It Does NOT Do

- no persistence
- no tool execution
- no agent planning
- no context compression
- no persona management

These belong to higher layers such as RohTalk, CLM, and future runtime systems.

---

## Usage Example

from Core.LLMClient.client import LLMClient

client = LLMClient()

result = client.chat(
    messages=[
        {"role": "user", "content": "Hello"}
    ],
    model="qwen3:1.7b",
    model_options={"think": False},
)

print(result.text)

Streaming example:

for event in client.chat_stream(
    [{"role": "user", "content": "Hello"}],
    model="qwen3:1.7b",
):
    if event.text_delta:
        print(event.text_delta, end="")

Collected streaming example:

result = client.chat_stream_collect(
    [{"role": "user", "content": "Hello"}],
    model="qwen3:1.7b",
)

print(result.text)
print(result.assistant_message)

---

## Relationship to RohTalk

LLMClient is the execution engine.

RohTalk is the runtime that:

- manages conversation history
- runs tool loops
- persists state
- exposes CLI behaviors through SkillCLI

LLMClient feeds RohTalk normalized outputs.

---

## Current Status

LLMClient currently supports:

- Ollama backend
- chat completion
- streaming responses
- tool call normalization
- assistant message normalization
- round-trip normalized message conversion

This is the stable foundation for local agent systems in NSP.
