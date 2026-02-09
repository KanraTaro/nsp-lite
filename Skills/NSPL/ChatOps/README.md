# Skills/ChatOps

Skills/ChatOps are the user-facing buttons for interacting with ChatOps.

These skills do not redefine the protocol. The protocol is defined in:
- Core/ChatOps/README.md

Skills/ChatOps exist to make it easy to:
- enqueue tasks
- run workers
- inspect queue state

## Quickstart workflows

### 1) Start a worker on a node

You run a worker on any node that should execute tasks.

Typical pattern:
- 1 or more workers per node
- workers watch the queue location for the chosen instance

### 2) Enqueue a task from anywhere

A producer can be:
- you manually running a skill
- a systemd timer
- a script
- a future GUI

It just writes a task JSON into Inbox/.

## Skill list (v1 target)

Names are placeholders. Actual names should match your SkillCLI naming conventions.

### ChatOps.send_task

Enqueue a task.

Inputs:
- --skill <SkillName>
- -- <args...> pass-through args for the target skill
- --instance <InstanceId>
- --node <NodeId> optional target
- --domain <Domain> optional routing tag
- --reply-to <Path> optional file result path

Output:
- writes task file to Inbox/
- prints task_id

### ChatOps.run_worker

Run a worker loop.

Inputs:
- --instance <InstanceId>
- --worker-id <WorkerId>
- --poll-ms <N> default value
- --once process a single task then exit

Output:
- consumes tasks from Inbox/
- writes result JSON
- moves tasks to Done/ or Failed/

### ChatOps.queue_status

Show queue stats.

Outputs:
- counts of Inbox/Claimed/Done/Failed
- optionally list newest N tasks

## Examples

Enqueue a task that runs a RohTalk skill:

ChatOps.send_task --instance main --skill RohTalk.send_prompt -- --persona default --text "hello"

Run a worker once (useful for tests):

ChatOps.run_worker --instance main --once

Check status:

ChatOps.queue_status --instance main

## How this ties into RohTalk

ChatOps does not need RohTalk to output task-shaped files.

Preferred pattern:
- ChatOps queues a task that calls RohTalk.send_prompt
- Worker executes the RohTalk skill
- RohTalk writes its own artifacts using NodeCTX
- Worker writes the ChatOps result file describing the run

This keeps ChatOps universal and keeps each app responsible for its own artifacts.

## First test skill recommendation

Before trusting send_prompt, validate the pipeline with a boring skill.

Good options:
- Forge.Time.now
  Writes a timestamp JSON and exits 0

- Tools.Echo.echo
  Writes a text file and exits 0

Keep one permanently. It is invaluable for debugging.

## What done looks like

Skills/ChatOps are done when:
- send_task reliably writes a valid task JSON
- run_worker reliably claims, executes, and finalizes tasks
- queue_status reads folders and reports accurately
- tests cover:
  - a happy path task
  - a failing task
  - schema validation failure

