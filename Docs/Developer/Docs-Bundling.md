# Docs Bundling

`NSPL.Docs.Bundle` generates pasteable Markdown context bundles from project documentation. The goal is to keep ChatGPT Projects, Claude Projects, Codex prompts, Claude Code sessions, and future contributor handoffs current without manually copying many files.

Generated bundle Markdown files are artifacts by default. Source docs and `bundles.json` are the committed truth; generated outputs such as `Docs/Bundles/*_CONTEXT.md` and `Docs/Bundles/PROJECT_CONTEXT.md` are ignored in this repo.

The skill is invoked through Entry. For repository bundles, run it from the repository root so manifest source paths resolve relative to the repo root:

```bash
python nspl.py skill NSPL.Docs.Bundle
```

## Default Behavior

The no-flag command does the most useful thing and generates only one bundle:

- if the target folder has `Docs/Bundles/bundles.json`, it generates that manifest's default bundle only
- otherwise, if the target folder has `Bundles/bundles.json`, it generates that manifest's default bundle only
- otherwise, it scans Markdown files and writes `Bundles/PROJECT_CONTEXT.md`

The target folder defaults to `NSPL_CALLER_CWD` when launched through `nspl.py --cwd`, otherwise the process current directory.

## Repo Mode

In NSPL repo-style projects, put the manifest at:

```text
Docs/Bundles/bundles.json
```

The NSPL repository manifest defines:

- `nspl-full`
- `nspl-public`
- `liferpg`
- `rohtalk`

`nspl-full` is the default bundle. It includes the main agent docs, developer docs, Scanner design doc, and known issues.

Useful commands:

```bash
python nspl.py skill NSPL.Docs.Bundle --list
python nspl.py skill NSPL.Docs.Bundle
python nspl.py skill NSPL.Docs.Bundle --bundle nspl-full
python nspl.py skill NSPL.Docs.Bundle --all
python nspl.py skill NSPL.Docs.Bundle --json --list
```

`--all` generates every configured bundle in the manifest. In the NSPL repo, those generated files are local artifacts and are ignored by Git.

## External Folder Mode

External creator, client, or project folders can use either a manifest at `Bundles/bundles.json` or auto mode.

From outside the NSPL repository:

```bash
cd /path/to/project
python /home/kanrataro/Projects/NSPLDev/nspl.py --cwd "$PWD" skill NSPL.Docs.Bundle
```

With no manifest, external folders use auto mode. This writes inside that target folder:

```text
Bundles/PROJECT_CONTEXT.md
```

To choose a target explicitly:

```bash
python nspl.py skill NSPL.Docs.Bundle --target /path/to/project --auto
python nspl.py skill NSPL.Docs.Bundle --target /path/to/project --output-name CUSTOM_CONTEXT.md
```

## Manifest Mode

A manifest declares named bundles with ordered source paths and optional safe globs. Globs are sorted alphabetically for stable output.

Minimal example:

```json
{
  "version": 1,
  "default": "project",
  "bundles": {
    "project": {
      "description": "Project context",
      "output": "Bundles/PROJECT_CONTEXT.md",
      "sources": [
        "README.md",
        "Docs/*.md",
        {"path": "Docs/Future.md", "optional": true}
      ]
    }
  }
}
```

Missing sources fail clearly unless a source entry is marked optional.

Future Scanner or bundling work may add manifest `source_root` or `base_dir` support so a manifest can resolve repo-root sources even when invoked from subfolders such as `Docs/`. For the MVP, run repo manifests from the repo root or pass the repo root as `--target`.

## Auto Mode

Auto mode ignores manifests and discovers Markdown files under the target:

```bash
python nspl.py skill NSPL.Docs.Bundle --auto
```

This is useful for quick packaging of external project folders that do not yet have curated bundle definitions.

## Excludes

Default excludes avoid runtime, generated, private, and noisy paths:

```text
State/
.git/
__pycache__/
.pytest_cache/
*.egg-info/
*.pyc
.venv/
venv/
node_modules/
.obsidian/
.trash/
.stfolder/
Bundles/
Docs/Bundles/*.md generated outputs
Docs/nsp-project-log-*.txt
nsp-project-log-*.txt
Logs/
logs/
Archive/
Archives/
Backups/
```

## Using Bundles With AI Tools

Use generated bundle Markdown as project context for ChatGPT Projects, Claude Projects, Codex prompts, Claude Code sessions, or human contributors. Refresh bundles after important milestone docs, reports, known issues, or architecture docs change.

Generated bundles are artifacts, not source truth. Edit the source docs first, record important development milestones in status docs or reports, then regenerate the bundle locally.
