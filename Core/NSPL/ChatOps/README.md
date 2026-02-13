# ChatOps (Core)

ChatOps is a filesystem-native task queue built on top of:

- SkillCLI (execution engine)
- NodeCTX (canonical routing + durable I/O)
- FPP (Filesystem Pulse Protocol)

ChatOps does not execute anything by itself.  
It defines the contract and primitives that make file-based automation safe, observable, and multi-node friendly.

If SkillCLI can run it, ChatOps can queue it.

---

# Design Philosophy

ChatOps is intentionally simple.

- Tasks are files.
- State transitions are folder moves.
- Results are JSON.
- The filesystem is truth.
- No hidden state.
- No in-memory queues.
- No database.

If a task exists on disk, it exists.
If it moves folders, it changed state.
If something fails, there is a breadcrumb.

---

# Dependency Direction

Core/ChatOps depends on:

- NodeCTX (routing + atomic I/O)

Skills/ChatOps depends on:

- Core/ChatOps
- SkillCLI

ChatOps does **not** depend on RohTalk, CLM, or any specific system.

It is infrastructure.

---

# Canonical Location

ChatOps queues are routed via NodeCTX:

```
State/<instance>/<scope>/Workflow/<domain>/
```

By default:

- bucket = "Workflow"
- domain = "ChatOps"
- global_scope = True

Which results in:

```
State/<instance>/Global/Workflow/ChatOps/
```

Inside that folder:

- Inbox/
- Claimed/
- Done/
- Failed/

All paths are produced through:

```
store.get_queue_dirs(...)
```

Never hardcode paths.

---

# Queue Directories

## Inbox/

Unclaimed task files.

Producers write here using `store.write_task()`.

## Claimed/

Tasks that have been atomically claimed by a worker.

Only one worker may successfully claim a file.

## Done/

Completed tasks.

Contains:

- original task file
- `<basename>.result.json`
- optional `<basename>.move_failed.txt` if transition move failed

## Failed/

Failed tasks.

Contains:

- original task file
- `<basename>.result.json`
- optional `<basename>.move_failed.txt`

---

# Atomic Claiming

Claiming is implemented in:

```
claim.py
```

It uses:

```
node_ctx.atomic_replace(...)
```

Properties:

- Atomic within same filesystem
- If two workers race, only one succeeds
- On failure, returns None
- On unexpected exception:
  - writes `<task>.claim_failed.txt` marker
  - returns None

No silent wedges.

---

# Task Schema (v1)

Validated by:

```
task_schema.validate_task(...)
```

Required fields:

- task_id (string)
- created_utc (ISO-8601 string)
- skill (string)
- args (list of strings)
- ctx (object)
  - instance_id (string)

Optional:

- ctx.node_id
- ctx.domain
- reply_to
- priority
- tags
- timeout_sec
- retries_max
- metadata

Unknown keys are allowed for forward compatibility.

Validation is strict and raises ValueError.

---

# Result Schema (v1)

Written by:

```
transitions.complete_task(...)
transitions.fail_task(...)
```

Result file name:

```
<task_basename>.result.json
```

Required result fields:

- task_id
- finished_utc
- status ("done" or "failed")
- exit_code
- worker_id
- skill
- args

Optional:

- duration_ms
- stdout
- stderr
- artifacts
- error

---

# State Transitions

Transition logic lives in:

```
transitions.py
```

Important behaviors:

- Result JSON is written first.
- Then task file is moved using `node_ctx.atomic_replace`.
- If move fails:
  - a `<basename>.move_failed.txt` marker is written
  - the system does not silently swallow the issue

Durability > elegance.

---

# Failure Safety

ChatOps enforces:

- No silent claim failures
- No silent move failures
- No silent schema failures
- All writes go through NodeCTX
- Atomic JSON writes
- Canonical routing

If something breaks, you can see it on disk.

---

# Ordering

`store.list_tasks(...)`:

- Returns only `.json` files
- Ignores `.result.json`
- Sorted by:
  - mtime
  - filename

Policy decisions (priority, scheduling, fairness) belong to the worker skill, not Core.

---

# Outbox / reply_to

ChatOps supports optional:

```
reply_to:
  mode: "file"
  path: "Outbox/<name>.json"
```

The worker:

- Forces all reply paths under Outbox/
- Writes via NodeCTX atomic write
- Logs reply_to_written or reply_to_failed

Outbox is optional and not required for base operation.

---

# What ChatOps Is NOT

ChatOps is not:

- A scheduler
- A DAG engine
- A distributed RPC layer
- A network service
- A message broker

It is a deterministic filesystem queue.

---

# Testing Coverage

Core tests verify:

- Schema validation
- Atomic claim behavior
- Double-claim prevention
- Basic durability assumptions

Run from repo root:

```
python run_tests.py
```

---

# Definition of Complete (v1)

ChatOps Core is considered complete when:

- Tasks validate correctly
- Claims are atomic
- Transitions write result before move
- Breadcrumb markers are written on unexpected errors
- Paths are routed exclusively through NodeCTX
- Tests pass on multiple platforms

Everything beyond this is orchestration, not infrastructure.

---

# Future (v2+)

Possible extensions:

- Retry policies
- Deferred/WrongTarget queue
- Priority queue semantics
- Cross-instance federation
- Structured observability tooling
- Backpressure controls

Core v1 stays minimal and deterministic.

---

# Summary

ChatOps is:

A thin, durable, canonical, filesystem-native execution layer.

It does one thing:

Turn files into executed SkillCLI calls.

And it does it safely.

