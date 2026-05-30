# Context Bundles

This folder contains the manifest for generated documentation bundles.

Bundles are derived artifacts. Edit source docs first, then regenerate bundle markdown only when needed.

## Manifest

`bundles.json` defines available bundles and their source paths/globs.

Current bundle names:

- `nspl-full`
- `nspl-public`
- `liferpg`
- `rohtalk`

## Hygiene Rules

- Do not include `State/`, `__pycache__/`, scan logs, or runtime files.
- Do not commit stale generated bundle outputs.
- Keep bundle definitions manifest-driven.
- Prefer explicit ordered source paths for project bundles.
