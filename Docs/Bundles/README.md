# Context Bundles

This folder contains the source manifest for generated documentation bundles.

Generated bundle Markdown files are local artifacts by default. Edit source docs first, record important milestones in status docs or reports, update `bundles.json` when bundle membership changes, then regenerate bundle markdown only when needed.

The committed source truth in this folder is:

- `README.md`
- `bundles.json`

## Manifest

`bundles.json` defines available bundles and their source paths/globs.

Current bundle names:

- `nspl-full`
- `nspl-public`
- `liferpg`
- `rohtalk`

## Hygiene Rules

- Do not include `State/`, `__pycache__/`, scan logs, or runtime files.
- Do not commit generated bundle outputs such as `*_CONTEXT.md` or `PROJECT_CONTEXT.md`.
- Keep bundle definitions manifest-driven.
- Prefer explicit ordered source paths for project bundles.
- Refresh generated bundles after milestone docs, reports, known issues, or architecture docs change.
- Run repository bundles from the repository root so manifest sources resolve relative to the project root.
