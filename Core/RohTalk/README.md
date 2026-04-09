# RohTalk Core (Pass 0)

This module provides the minimal infrastructure needed to support a
chat‑style agent in NSP Lite.  It is deliberately small and
opinionated, focusing on a single conversation pipeline without any
tool loop.  Higher level features such as tool execution, persona
management or long running sessions are intentionally out of scope for
Pass 0.

## What it does

* **Configuration** – Loads persistent defaults (agent name, system
  identity, model and host) from `State/<Instance>/<Scope>/Config/RohTalk/config.json`
  or `Config/RohTalk/config.json`, falling back to hard‑coded values.
* **Message assembly** – Prepends a system message containing the
  agent identity before the user’s prompt.
* **Conversation storage** – Writes a JSON metadata file and an
  append‑only JSONL event log into
  `State/<Instance>/<Scope>/Workflow/RohTalk/Conversations/` for each
  conversation.  Metadata includes the entire message history so that
  subsequent turns can be constructed without reading the event log.
* **Conversation lifecycle** – Supports creating a new conversation or
  appending a message to an existing one.  Onesho
  conversations are stored in the same way but are excluded from
  listings by default.
* **Unified runner** – Exposes a single `run_conversation()` helper
  that hides the distinction between creation and append.  Skills use
  this to implement `oneshot` and `chat` behaviours.

## What it doesn’t do

* No tool execution.  The assistant’s replies come directly from the
  model.
* No streaming responses.  Only the final reply text is returned.
* No ChatOps integration or chat loops.
* No persona registry beyond the single identity string in the config.
* No GUI or interactive prompt loop.

## File layout

```
Core/RohTalk/
  __init__.py     # Public exports
  config.py       # Load and merge configuration values
  messages.py     # Helpers for assembling message payloads
  conversations.py# Durable conversation storage and retrieval
  runner.py       # High level orchestration for one turn
  Tests/          # Offline unit tests
```

### On‑disk storage

All persistent state lives in the `State/` directory via NodeCTX.
Under a given instance and node scope conversations are stored as:

```
State/<Instance>/<Scope>/Workflow/RohTalk/Conversations/
  <conversation_id>.json            # Metadata (created_at, updated_at, messages, kind)
  <conversation_id>.events.jsonl    # Append‑only message/event log
```

File names are automatically prefixed according to NodeCTX settings
(`NODECTX_ENABLE_PREFIXING`, `NODECTX_PREFIX_INSTANCE` etc.) to
preserve provenance when files are moved off node.  The conversation
identifier returned by the API does **not** include the prefix.

### Configuration files

User‑supplied defaults can be stored in:

1. `State/<Instance>/<Scope>/Config/RohTalk/config.json`
2. `Config/RohTalk/config.json` (repository root)

Both files accept a JSON object with any of the following keys:

* `agent_name` – Human friendly name for the agent (string)
* `agent_identity` – System prompt injected into every conversation (string)
* `default_model` – Model name used when callers do not specify one (string)
* `default_host` – Optional backend URL override (string or null)

Unknown keys are ignored.  Missing keys fall back to hard‑coded
defaults (`RohTalk`, a generic assistant identity, and `qwen3:0.6b`).

## Usage examples

While the core API is intended for Skills, it can be exercised
directly for testing or scripting.  The following example creates a
conversation, appends a message and lists conversations:

```python
from Core.NSPL.SkillCLI.ctx import SkillContext
import Core.NSPL.NodeCTX as NodeCTX
from Core.RohTalk import create_conversation, append_message, list_conversations

# Construct a minimal context (normally provided by SkillCLI)
ctx = SkillContext(
    root=Path("/path/to/repo"),
    node_tag="MyNode",
    instance_id="main",
    global_scope=False,
    node_ctx=NodeCTX,
    debug=False,
    json=False,
)

# Create a new conversation
conv_id, reply = create_conversation(ctx, "Hello world!")
print(f"Assistant: {reply}")

# Send another message
reply2 = append_message(ctx, conv_id, "How are you?")
print(f"Assistant: {reply2}")

# List stored conversations
for meta in list_conversations(ctx):
    print(meta["id"], meta["updated_at"])
```

## See also

* `Skills/RohTalk/README.md` – contains user‑facing examples for the
  oneshot, chat and list_conversations skills.
* `Core/NSPL/NodeCTX/README.md` – details on canonical path routing and
  durable writes.
* `Core/LLMClient/README.md` – describes how the model client works and
  what exceptions to expect.