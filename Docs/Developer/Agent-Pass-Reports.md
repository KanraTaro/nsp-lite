# Agent Pass Reports

Use pass reports to make agent work auditable and easy to continue.

## Where Reports Go

```text
Docs/Reports/Codex/
Docs/Reports/Claude/
Docs/Reports/Human/
```

Use a dated filename when saving a report, for example:

```text
Docs/Reports/Codex/2026-05-30-docs-hygiene.md
```

Do not put private notes, secrets, personal data, or runtime state in repo reports.

## Required Format

```markdown
# Agent Pass Report

## Pass Name

## Goal

## Files Changed

## Core/Skill/Web/GUI Impact

## User-Facing Changes

## State/Data Changes

## Tests Run

## Manual Smoke

## Deferred Work

## Risks / Known Issues

## Suggested Next Pass
```

## What Must Be Reported

- files changed
- whether Core, Skills, Web, GUI, docs, or state behavior changed
- commands run and results
- skipped validation
- manual smoke notes for Web/GUI work
- generated files created or removed
- remaining debt or uncertainty
