# Skills/ChatOps

Skills/ChatOps are the user-facing entrypoints for interacting with the ChatOps filesystem queue.

Protocol + schema + core behavior live in:
- Core/NSPL/ChatOps/README.md

These skills exist to make it easy to:
- enqueue tasks (producer)
- run a worker loop (worker)
- inspect queue state (observer)

---

## Skills

### ChatOps.send_task

Enqueue a task file into the ChatOps Inbox.

This does not execute the task. It writes a validated task JSON and exits.

Key flags:

- `--instance <InstanceId>` (SkillCLI flag)
- `--skill <SkillName>` required
- `--target <NodeId>` optional, sets `ctx.node_id`
- `--ctx-domain <Domain>` optional, sets `ctx.domain`
- `--domain <ChatOpsDomain>` optional, selects queue location (default: ChatOps)
- `--reply-to <Path>` optional, stored as `reply_to.path`
- `--` then any remaining tokens are passed through as the target skill args

Example:

python -m Core.NSPL.SkillCLI skill ChatOps.send_task \
  --instance main \
  --skill Tools.Echo.echo \
  --target KanraDesktop \
  --reply-to Outbox/example.result.json \
  -- hello world

---

### ChatOps.run_worker

Run a worker loop that:

- scans Inbox/
- atomically claims a task into Claimed/
- validates task schema
- executes the target skill via SkillCLI
- writes a result JSON
- moves the task into Done/ or Failed/

Key flags:

- `--domain <ChatOpsDomain>` selects queue location (default: ChatOps)
- `--worker-id <Id>` optional identifier used for logs/results
- `--poll-ms <N>` polling interval when idle
- `--once` process at most one task then exit (useful for tests)

Notes:

- Tasks can be targeted using `ctx.node_id`. If the task targets a different node, the worker attempts to return it to Inbox.
- Worker events are written via NodeCTX to `State/<instance>/Global/Logs/<domain>/worker/<worker_id>.events.jsonl`
- Disk safety knobs:
  - `--idle-heartbeat-sec` (throttled idle heartbeats)
  - `--log-max-bytes`, `--log-keep` (jsonl rotation)

Example (run one task then exit):

python -m Core.NSPL.SkillCLI skill ChatOps.run_worker \
  --instance main \
  --once \
  --poll-ms 0

---

### ChatOps.queue_status

Print the queue counts for a given instance/domain.

Counts are derived from the filesystem:

- Inbox / Claimed: counts task JSON files (excluding `*.result.json`)
- Done / Failed: counts result files (`*.result.json`)

Key flags:

- `--domain <ChatOpsDomain>` selects queue location (default: ChatOps)

Example:

python -m Core.NSPL.SkillCLI skill ChatOps.queue_status \
  --instance main \
  --domain ChatOps

---

## Quickstart

### 1) Start a worker

Run a worker on any node that should execute tasks:

python -m Core.NSPL.SkillCLI skill ChatOps.run_worker \
  --instance main \
  --domain ChatOps

### 2) Enqueue tasks from anywhere

A “producer” can be you, a script, a timer, or a future UI.

All it does is write task JSON files into Inbox.

---

## What “done” looks like (Skills)

Skills/ChatOps is considered healthy when:

- send_task writes a valid task JSON into Inbox
- run_worker claims + executes + finalizes tasks reliably
- queue_status reports accurate counts
- tests cover:
  - a happy path task
  - a failing task
  - basic smoke coverage

