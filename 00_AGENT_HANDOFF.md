# NSPLDev Agent Handoff

## Role

You are an implementation worker for NSPLDev.

Do not act as the architect. Do not redesign systems unless explicitly asked.

## Core Architecture Rules

- Filesystem state is authoritative.
- Prefer small, testable, reversible edits.
- Skills are thin CLI entrypoints.
- Core owns reusable logic.
- SkillCLI is the official way to invoke skills.
- Do not bypass NodeCTX for durable state.
- Do not add databases, brokers, hidden daemons, or external services unless explicitly requested.
- Do not change public imports or folder structure unless explicitly requested.
- Preserve existing behavior unless the task says otherwise.
- Use explicit typing where practical.
- Keep inline comments concise and practical.
- Do not use broad “cleanup” refactors.

## Current Patterns

- Core/AutoRoh contains reusable AutoRoh logic such as state and policy.
- Skills/AutoRoh/run/skill.py should orchestrate, not own reusable policy.
- Core/RohTalk owns conversation/tool loop behavior.
- Core/RohTalk/tracing.py owns reusable console trace helpers.
- Toolkits expose model-facing tools.
- AutoRoh can run forever, idle-skip, call an observation tool, trace tools, and record tool actions.

## Validation

For Python edits, run:

python -m py_compile <changed files>

When relevant, run the project test harness if available.

## Output

After edits, report:
- files changed
- what changed
- commands run
- any failures or uncertainty
