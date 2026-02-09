# NSP Lite

NSP Lite is a minimal, test-driven Python framework for filesystem-driven automation.

Tasks, state, and logs live directly on disk. This makes the system portable, inspectable, crash-safe, and naturally multi-node when used with a shared or synchronized filesystem (Syncthing, NFS, rsync, etc).

There is no database, no message broker, and no long-running service required to understand system state.
The filesystem is the source of truth.

This repository is a clean, public slice of a larger architectural approach focused on durable automation primitives that scale outward by sharing state, not by adding infrastructure.

---

## What this repository demonstrates

### SkillCLI
A lightweight CLI layer that discovers runnable skills from skill.json metadata.

- Safe discovery without importing every module
- Explicit, testable skill execution
- Consistent interface for local automation

### ChatOps (filesystem-backed task queue)
A durable, disk-based job queue implemented entirely with files and atomic operations.

- Producers write task JSON files into Inbox/
- Workers atomically claim tasks via rename into Claimed/
- Skills are executed through SkillCLI
- Results are written durably to:
  - Done/ (archival task + result)
  - Outbox/ (optional reply_to writeback)
- Workers emit structured JSONL event logs for observability

### NodeCTX
Filesystem and logging utilities that support safe automation:

- Atomic JSON writes
- Durable JSONL append
- Centralized logging funnel with optional throttling and rotation

---

## Quickstart

### Requirements
- Python 3.10+ (3.11+ recommended)

From the repository root:

python demo.py

The demo performs a deterministic end-to-end run:

1. Wipes State/ so the run is repeatable
2. Runs the full test suite
3. Lists discovered skills
4. Enqueues a task into the filesystem queue
5. Runs a worker once to claim and execute the task
6. Prints exact artifact locations and outputs

This script is the primary demonstration for this repository.

---

## Running tests

python run_tests.py

All core behavior is covered by unit tests and end-to-end tests, including task claiming, execution, result persistence, and logging.

---

## Common commands

List discovered skills:

python -m Core.NSPL.SkillCLI list

Run a skill directly:

python -m Core.NSPL.SkillCLI skill <SkillName> --instance main -- <args>

Enqueue a task (producer):

python -m Core.NSPL.SkillCLI skill ChatOps.send_task --instance main --skill Tools.Echo.echo --reply-to Outbox/demo_result.json -- Hello from README

Run the worker once (consumer):

python -m Core.NSPL.SkillCLI skill ChatOps.run_worker --instance main --once --idle-heartbeat-sec 1.0 --quiet-idle

Check queue status:

python -m Core.NSPL.SkillCLI skill ChatOps.queue_status --instance main

---

## On-disk layout

After running demo.py, proof artifacts appear under State/.

Workflow queues:

State/<instance>/Global/Workflow/ChatOps/
  Inbox/      tasks waiting to be processed
  Claimed/    tasks currently claimed
  Done/       completed tasks plus result JSON
  Failed/     failed tasks plus result JSON
  Outbox/     reply_to writeback files

Worker event logs (JSONL):

State/<instance>/Global/Logs/ChatOps/worker/
  <worker_id>.events.jsonl

Event logs capture state transitions and execution events such as claimed, exec_start, exec_done, and reply_to_written.

---

## Why filesystem-driven?

Filesystem-driven automation provides:

- Inspectability (every task, result, and log is readable with standard tools)
- Durability (state survives crashes)
- Portability (runs anywhere Python runs)
- Multi-node coordination via atomic file operations

The goal is not to reimplement large distributed systems, but to build automation primitives that are simple enough to trust, debug, and evolve.

---

## Repository layout (high level)

Core/
  SkillCLI/        skill discovery and runner CLI
  ChatOps/         task schema, queue store, transitions
  NodeCTX/         filesystem and JSONL logging utilities
Skills/
  ChatOps/         send_task, run_worker, queue_status
  Forge/           example skills used by the demo
State/             runtime output (generated, gitignored)
demo.py            deterministic end-to-end demo
run_tests.py       test runner

---

## License

MIT License.

