# RohTalk Skills

This directory exposes RohTalk Core through user-facing CLI skills.

All skills are executed through SkillCLI and operate on the same persistent conversation system.

---

## Core Concept

RohTalk skills are the interface layer for:

- starting conversations
- continuing conversations
- inspecting stored state
- deleting or clearing sessions
- testing tool-enabled behavior

All persistent conversation state is stored on disk through NodeCTX.

---

## Available Skills

### RohTalk.start

Start a new persistent conversation.

Supports:

- automatic title generation
- optional model override
- optional host override
- optional model profile with `--model-profile`
- repeatable model runtime options with `--model-option key=value`
- optional tool loop execution with `--tools`

Usage:

python nspl.py skill RohTalk.start -- "Hello"

Tool-enabled:

python nspl.py skill RohTalk.start --tools -- "What's the weather in Orlando?"

Output:

- `conversation_id`
- `title`
- assistant reply

---

### RohTalk.chat

Continue an existing conversation.

Supports:

- full conversation id
- numeric index from `RohTalk.list_conversations`
- optional model override
- optional host override
- optional model profile with `--model-profile`
- repeatable model runtime options with `--model-option key=value`
- optional tool loop execution with `--tools`

Usage:

python nspl.py skill RohTalk.chat 0 -- "How are you?"

Tool-enabled:

python nspl.py skill RohTalk.chat --tools 0 -- "What's the weather like in New York?"

Model profile example:

python nspl.py skill RohTalk.chat --model-profile dst_director_fast 0 -- "Keep this fast"

---

### RohTalk.oneshot

Run a single-turn prompt without creating a long-lived chat thread.

The interaction is still stored as a conversation with kind `oneshot`, but oneshots are hidden from default listings.

Usage:

python nspl.py skill RohTalk.oneshot -- "Quick question"

---

### RohTalk.list_conversations

List stored conversations.

By default, oneshot conversations are hidden.

Each line prints:

[index] title | short_id | updated_timestamp | full_id

Usage:

python nspl.py skill RohTalk.list_conversations

Include oneshots:

python nspl.py skill RohTalk.list_conversations --include-oneshots

---

### RohTalk.show_conversation

Display a stored conversation in readable form.

Usage:

python nspl.py skill RohTalk.show_conversation 0

or:

python nspl.py skill RohTalk.show_conversation <conversation_id>

---

### RohTalk.delete_conversation

Delete a stored conversation by id or numeric index.

Usage:

python nspl.py skill RohTalk.delete_conversation 0

Include oneshots for numeric index resolution:

python nspl.py skill RohTalk.delete_conversation --include-oneshots 0

---

### RohTalk.clear_oneshots

Delete all stored oneshot conversations.

Usage:

python nspl.py skill RohTalk.clear_oneshots

Preview only:

python nspl.py skill RohTalk.clear_oneshots --dry-run

---

### RohTalk.tool_test

Proving skill for tool-enabled execution.

This skill:

- runs the tool loop without persistence
- is useful for backend testing
- is useful for prompt/tool-definition testing
- can stream visible activity unless `--quiet` is used

Usage:

python nspl.py skill RohTalk.tool_test -- "What's the weather in Orlando?"

Quiet mode:

python nspl.py skill RohTalk.tool_test --quiet -- "What's the weather in Orlando?"

Show final normalized history:

python nspl.py skill RohTalk.tool_test --show-history -- "What's the weather in Orlando?"

### RohTalk.benchmark

Run repeatable benchmark smoke cases for comparing RohTalk model and profile
options without changing default config or Operator Station behavior.

Supports:

- optional `--model`, `--model-profile`, and `--host`
- repeatable `--model-option key=value`
- optional `--toolkit`, repeatable `--case`, and explicit `--tools`/`--no-tools`
- modes: `no-tools`, `tool-dry`, `dst-director-dry`, and `dst-director-live`
- JSON output with `--json`
- JSONL and markdown save under RohTalk Logs with `--save`

Safe defaults:

python nspl.py skill RohTalk.benchmark --mode no-tools --suite smoke --iterations 1

Model comparison examples:

python nspl.py skill RohTalk.benchmark --model gpt-oss:20b --mode no-tools --json

python nspl.py skill RohTalk.benchmark --model gemma4:e2b --mode no-tools --json

python nspl.py skill RohTalk.benchmark --model gemma4:12b --mode dst-director-dry --toolkit dst_director --json

python nspl.py skill RohTalk.benchmark --model-profile dst_director_fast --mode dst-director-dry --toolkit dst_director --json

python nspl.py skill RohTalk.benchmark --model-profile dst_director_quality --mode dst-director-dry --toolkit dst_director --json

Live DST actions are blocked unless explicitly enabled:

python nspl.py skill RohTalk.benchmark --mode dst-director-live --allow-live-dst-actions

### RohTalk.shell

Run an interactive shell against a persistent conversation.

Supports:

- creating or attaching to a conversation
- optional `--tools`
- named `--toolkit`
- `--watch` read-only mode for external messages
- `/note TEXT` injection without running a model turn
- `/refresh`, `/recent`, and `/history`

Usage:

python nspl.py skill RohTalk.shell

Attach with tools:

python nspl.py skill RohTalk.shell --conversation 0 --tools --toolkit basic

Watch an existing conversation:

python nspl.py skill RohTalk.shell --conversation 0 --watch

---

## Tool Behavior

When `--tools` is enabled:

1. the tool-capable loop is used instead of a single model call
2. assistant tool-call messages are appended to normalized history
3. tools are executed
4. tool result messages are appended
5. the model is called again with updated history
6. the final assistant response is persisted

This enables:

- grounded answers
- multi-step reasoning
- persistent tool-aware conversations

---

## Suggested CLI Flow

Start a persistent conversation:

python nspl.py skill RohTalk.start -- "Hello"

Start a tool-enabled conversation:

python nspl.py skill RohTalk.start --tools -- "What's the weather in Orlando?"

List conversations:

python nspl.py skill RohTalk.list_conversations

Inspect one:

python nspl.py skill RohTalk.show_conversation 0

Continue it:

python nspl.py skill RohTalk.chat 0 -- "How are you?"

Continue with tools:

python nspl.py skill RohTalk.chat --tools 0 -- "What's the weather in New York?"

---

## Storage Location

All persistent RohTalk data is stored through NodeCTX:

State/<Instance>/<Scope>/RohTalk/Workflow/Conversations/

Each conversation has:

- metadata JSON containing full normalized history
- append-only JSONL event log

Context can be overridden through standard SkillCLI flags:

- `--instance`
- `--node`
- `--global`

---

## Design Principles

### CLI is the Primary Interface

All skills run through SkillCLI.

This gives:

- consistent invocation
- shared runtime context
- compatibility with future automation

---

### Conversations are Persistent

State is not hidden in memory.

Conversations can be resumed, inspected, and replayed from disk.

---

### Tool Loop is Optional

- default behavior = simple single-turn model call
- `--tools` = multi-step tool-capable reasoning loop

This keeps the basic CLI simple while allowing richer agent behavior when needed.

---

### Model Runtime Options

RohTalk loads `default_model`, `default_options`, and named `profiles` from
`Config/RohTalk/config.json` or the State override config. Profiles can set a
model, host, and provider options. For Ollama, options are sent as top-level
request fields, which supports fast local settings such as `think=false`.

Examples:

python nspl.py skill RohTalk.start --model-profile dst_director_fast -- "Hello"

python nspl.py skill RohTalk.shell --model-profile dst_director_quality

python nspl.py skill RohTalk.chat --model-option think=false 0 -- "Short answer"

---

### Execution is Moving Toward Unification

RohTalk can execute model-requested tools through SkillCLI-backed skills.
Named toolkits expose model-facing tool definitions and map those names back
to canonical SkillCLI skill names. Local in-process callables remain available
as a bootstrap/testing backend.

This gives one execution surface for:

- humans using SkillCLI
- agents using RohTalk tool loops
- automation workers

---

## Current Status

RohTalk Skills currently support:

- persistent conversations
- tool-enabled start/chat flows
- oneshot prompts
- conversation inspection
- conversation deletion and cleanup
- tool-loop proving via `RohTalk.tool_test`
- interactive persistent shell/watch workflows via `RohTalk.shell`

---

## Relationship to Core

Skills are thin wrappers.

Core handles:

- message assembly
- conversation persistence
- tool loops
- normalized history
- backend interaction through LLMClient

Skills handle:

- CLI argument parsing
- output formatting
- user-facing entrypoints

---

## Notes

Current implementation still has some temporary proving-layer duplication:

- weather tool definition is duplicated across tool-enabled skills
- local callable tool execution still exists as a bootstrap/testing backend
- tool-call rendering in `show_conversation` can still be improved

These are known next-step cleanup items, not architectural blockers.

---

## Next Steps

Planned follow-up work:

- centralize shared tool definitions
- improve `show_conversation` rendering for tool calls
- add profile-based backend capability handling
- expand streaming visibility into more user-facing skills
