# ChatOps

ChatOps is a file-based task queue + worker runtime that executes SkillCLI skills on one or more nodes.

ChatOps is not "automation" by itself. It is the plumbing that makes automation possible by letting anything enqueue tasks and letting workers claim and run them in a predictable, auditable way.

## Goals

- Provide a universal task format that can run any SkillCLI skill.
- Use filesystem as truth (FPP). No hidden state.
- Support multi-node and multi-worker execution safely.
- Keep dependency direction clean:
  - Skills/ChatOps -> Core/ChatOps
  - ChatOps does not depend on RohTalk.

## Non-goals (v1)

- DAG workflows, task graphs, or fancy orchestration
- Built-in scheduling (cron/systemd can enqueue tasks if needed)
- Remote networking layer (filesystem + your sync layer handle that)
- UI (UI can be built later by reading queue state and calling skills)

## Concept model

ChatOps has 3 main roles:

- Producer: anything that writes a task file into the inbox
- Worker: a loop that claims tasks and runs them via SkillCLI
- Observer: anything that reads the queue folders to show status and results

## Directory layout

ChatOps lives inside a NodeCTX routed location, meaning it should be stored in the correct State/<InstanceId>/... structure for your instance and scope.

Core idea: tasks are files, state transitions are folder moves.

Recommended layout under the ChatOps root:

- Inbox/
  Unclaimed tasks. Producers write here.

- Claimed/
  Tasks claimed by a worker. Claiming should be atomic.

- Done/
  Completed tasks with a result record.

- Failed/
  Tasks that failed, with a result record.

- Outbox/
  Optional, if you want responses separated from task files. Many systems store the result next to the task.

- Logs/
  Worker logs, if you want them.

ChatOps does not require a specific filename format, but it helps if tasks use:
- a timestamp prefix
- a short slug
- a unique id

Example:
2026-01-20_13-42-05__send_prompt__d7c8f3a1.json

## Task file schema (v1)

A ChatOps task is a JSON file that describes a SkillCLI invocation.

Required fields:

- task_id (string)
- created_utc (string, ISO-8601)
- skill (string, canonical SkillCLI skill name)
- args (array of strings)
- ctx (object)
  - instance_id (string)
  - node_id (string, optional)
  - domain (string, optional)
- reply_to (object, optional)
  - mode (string: file)
  - path (string)

Optional fields:

- priority (integer, default 0)
- tags (array of strings)
- timeout_sec (integer, optional)
- retries_max (integer, default 0)
- metadata (object, arbitrary)

Example task JSON:

{
  "task_id": "d7c8f3a1",
  "created_utc": "2026-01-20T18:42:05Z",
  "skill": "RohTalk.send_prompt",
  "args": ["--persona", "default", "--text", "Summarize today's logs"],
  "ctx": {
    "instance_id": "main",
    "node_id": "KanraAlly",
    "domain": "RohTalk"
  },
  "reply_to": {
    "mode": "file",
    "path": "Outbox/d7c8f3a1.result.json"
  },
  "priority": 0,
  "tags": ["rohtalk", "prompt"]
}

Notes on skill and args:
ChatOps does not interpret args. It passes them through to SkillCLI.
Interoperability comes from a single universal contract:
If SkillCLI can run it, ChatOps can queue it.

## Result file schema (v1)

A ChatOps result is a JSON file describing what happened when the worker ran the skill.

Required fields:

- task_id (string)
- finished_utc (string, ISO-8601)
- status (string: done or failed)
- exit_code (integer)
- worker_id (string)
- skill (string)
- args (array of strings)

Optional fields:

- duration_ms (integer)
- stdout (string, optional, can be truncated)
- stderr (string, optional, can be truncated)
- artifacts (array of objects, optional)
  - example: { "kind": "file", "path": "State/main/.../some_output.json" }
- error (object, optional)
  - type, message, trace

Example result JSON:

{
  "task_id": "d7c8f3a1",
  "finished_utc": "2026-01-20T18:42:09Z",
  "status": "done",
  "exit_code": 0,
  "duration_ms": 3562,
  "worker_id": "KanraDesktop:worker-01",
  "skill": "RohTalk.send_prompt",
  "args": ["--persona", "default", "--text", "Summarize today's logs"],
  "stdout": "",
  "stderr": "",
  "artifacts": [
    { "kind": "file", "path": "State/main/Global/Data/RohTalk/Prompts/d7c8f3a1.prompt.json" },
    { "kind": "file", "path": "State/main/Global/Data/RohTalk/Responses/d7c8f3a1.response.json" }
  ]
}

## Worker lifecycle

A worker loops:

1. Scan Inbox/ for tasks
2. Pick a task (priority and ordering are policy)
3. Claim it atomically by moving it to Claimed/
4. Execute the task via SkillCLI
5. Write a result JSON
6. Move the task (and/or result) to Done/ or Failed/

Claiming must be atomic.
Simplest safe claim is filesystem rename/move within the same filesystem.
If two workers race, only one should succeed.

## Failure, retries, idempotency

- v1 can default to retries_max = 0
- If retries exist, the worker must treat tasks as potentially repeated
- Skills should be safe to re-run where possible

Core/ChatOps does not "undo" anything. Filesystem is truth.

## Integration points

Core/ChatOps integrates with:

- SkillCLI (required)
- NodeCTX (recommended) for routing queue location and writing artifacts
- FPP (required philosophy) for auditability and UI friendliness

## Complete ChatOps, defined

Complete ChatOps means:

- A stable schema for tasks and results
- A working worker loop with atomic claims
- A producer skill that enqueues tasks
- Tests proving:
  - claim behavior works
  - result files get written
  - done/failed transitions happen
  - schema validation catches bad tasks
- Docs that match behavior

Anything beyond that is ChatOps v2.

