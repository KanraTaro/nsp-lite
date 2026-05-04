# NSPLDev Agent Instructions

## Always read first

- Read this file before making changes.
- If `00_AGENT_HANDOFF.md` exists, read it next. Treat it as the active pass contract.
- If this file and the handoff conflict, stop and ask unless the handoff explicitly says it supersedes a repo rule.

## Architecture rules

- Core modules own reusable logic, contracts, validation, and policy.
- Skills are thin SkillCLI entrypoints.
- SkillCLI is the execution surface for humans, agents, and automation.
- RohTalk toolkits expose model-facing tools mapped to canonical SkillCLI skills.
- AutoRoh should use profiles/toolkits/policy, not hardcoded workflow behavior.
- Do not expose low-level raw command writers to model toolkits unless explicitly requested.

## Change rules

- Make small, testable, reversible changes.
- Do not touch unrelated domains.
- Preserve existing public skill names unless the handoff explicitly allows migration.
- Add or update tests for behavior changes.
- Update README files when behavior or command surfaces change.
- Do not commit generated scan logs such as `nsp-project-log-*`.

## Validation

- Run focused tests for touched modules.
- Run `python run_tests.py` after behavior changes when practical.
- Report commands run and any skipped validation honestly.
