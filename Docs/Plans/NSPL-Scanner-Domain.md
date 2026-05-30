# NSPL Scanner Domain

## Purpose

`NSPL.Scanner` is a future platform domain for scanning, indexing, exporting, and safely packaging folders and repositories.

This pass does not implement Scanner. It documents the intended domain boundary so the current `NSPL.Docs.Bundle` MVP can stay small and independent.

## Domain Boundary

Scanner understands folder structure and produces reports, indexes, privacy checks, diffs, manifests, and exports.

Docs.Bundle produces curated pasteable Markdown context bundles from project docs.

Scanner can later feed Docs.Bundle with discovered file sets or generated indexes, but Docs.Bundle MVP must not depend on Scanner.

## Future Skills

`NSPL.Scanner.Scan`
: Scan a target folder, apply default excludes, collect file metadata, and write a durable report.

`NSPL.Scanner.Tree`
: Produce a readable tree view with noisy folders omitted.

`NSPL.Scanner.Index`
: Build machine-readable indexes of files, sizes, types, timestamps, and selected content hints.

`NSPL.Scanner.Export`
: Export selected files or reports into portable context packages.

`NSPL.Scanner.Privacy`
: Flag likely private or unsafe-to-share files before packaging.

`NSPL.Scanner.Diff`
: Compare two scans or scan reports and show changed, added, removed, and suspicious files.

`NSPL.Scanner.Manifest`
: Generate or update candidate bundle/export manifests from scanned structure.

`NSPL.Scanner.Summarize`
: Produce concise summaries of scanned folders for humans and agents.

## Legacy Reference

There is an older Bash `nsp-scan` workflow that scans folders, lists trees/files, dumps text content, skips noisy dirs/globs, truncates long files, and writes `nsp-project-log` files.

The future Scanner domain should replace that workflow cleanly later. It should preserve the useful behavior while moving policy, exclusions, privacy checks, and output contracts into tested Core logic and thin Skills.

## Relationship To Docs.Bundle

Docs.Bundle should remain a docs-focused packaging tool:

- manifest bundles for curated project context
- auto Markdown bundles for quick external folders
- stable Markdown output for ChatGPT, Claude, Codex, Claude Code, and contributors
- no hardcoded source paths in Python
- no Scanner dependency in the MVP

Scanner should eventually support broader folder intelligence:

- non-Markdown indexes
- truncation policy
- privacy reports
- file trees
- generated manifests
- diffable scan reports
- richer exports

## Milestone Practice

Important development milestones should be recorded in status docs or reports under `Docs/Reports/`. After milestone docs change, generated context bundles should be refreshed so ChatGPT and Claude Project context stays current.
