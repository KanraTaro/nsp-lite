# Entry WebUI Refactor Plan

## Revision Note

This is a historical implementation plan. The Entry consolidation, Web launch
surface, `Web/NSPL/Status` reference app, optional Web dependencies, and
WebContext subprocess-backed skill invocation have now landed. Current
developer-facing architecture docs live in:

- `README.md`
- `Core/NSPL/README.md`
- `Core/NSPL/Entry/README.md`
- `Web/README.md`
- `Docs/Developer/Entry-Surfaces.md`

This revision changes the plan from "add WebHost beside existing CLIs" to "consolidate command surfaces under `Core/NSPL/Entry` while preserving compatibility." The target is one NSPL Entry with many surfaces: `skill` for one-shot actions, `gui` for desktop/native visual shells, `web` for browser/mobile visual shells, and possibly `app` later.

## Current Architecture Summary

`nspl.py` is currently the real root-level NSPL gateway entrypoint. It owns bootstrap and forwarding:

- Computes repo root from the directory containing `nspl.py`, unless `--root` is supplied.
- Accepts `--cwd` as caller working-directory context.
- Validates that the repo root contains `Core/`.
- Validates that caller cwd exists.
- Inserts repo root into `sys.path`.
- Exports `NSPL_CALLER_CWD`.
- Changes cwd to repo root while forwarding so ProjectRoot discovery is stable.
- For `skill`, imports `Core.NSPL.SkillCLI.skillcli.main`, strips literal `--`, and forwards remaining args.
- For `gui`, imports `Core.NSPL.GUICLI.guicli.main`, strips literal `--`, and forwards remaining args.

Current SkillCLI behavior:

- Package: `Core/NSPL/SkillCLI`.
- Module invocation: `python -m Core.NSPL.SkillCLI <command>`.
- Commands: `list [--detailed]` and `skill <SkillName> [args...]`.
- Default discovery root: `Skills/`, overridable by `SKILLS_ROOT`.
- Discovery scans recursively for `skill.json`.
- Discovery ignores empty, whitespace-only, broken, or incomplete descriptors.
- Valid descriptors require `name`, `version`, and `description`; `entry` defaults to `skill.py`.
- `list` does not import skill modules.
- Running a skill imports exactly one module, validates `build_parser(parser)` and `run(args, ctx)`, builds the standard SkillCLI context, and emits best-effort NodeCTX lifecycle logs.

Current GUICLI behavior:

- Package: `Core/NSPL/GUICLI`.
- Module invocation: `python -m Core.NSPL.GUICLI ...`.
- Commands: `list [--detailed]` and `run <GuiName> [argv...]`.
- Default discovery root: `GUI/`, overridable by `GUI_ROOT`.
- Discovery scans recursively for `gui.json`.
- Discovery ignores empty, whitespace-only, broken, or incomplete descriptors.
- Valid descriptors require `name`, `version`, and `description`; `entry` defaults to `launch.py`.
- `list` does not import GUI modules.
- Running a GUI imports exactly one module, validates `main(argv=None)`, strips a leading passthrough `--` if present, and emits best-effort NodeCTX lifecycle logs.

Current docs and conventions:

- `README.md` defines domains across `Core/`, `Skills/`, `Config/`, and `GUI/`.
- `Core/NSPL/README.md` defines filesystem truth, explicit execution, no hidden background services, no databases or brokers as source of truth, and GUI shells rather than alternate execution engines.
- `Core/NSPL/SkillCLI/README.md` documents SkillCLI as the stable dispatcher for skills.
- `GUI/Video/LookLab/README.md` documents GUICLI discovery and explicitly calls out the future web lane as something that should reuse Core and Skill surfaces.

External local wrappers:

- Wrapper scripts are external launch conveniences, not internal architecture.
- A generic wrapper command should preserve Entry surface syntax: `nspl skill list`, `nspl skill <SkillName> [args...]`, and `nspl web list`.
- A wrapper can resolve dev/prod root and invoke `python3 "$ROOT/nspl.py" --root "$ROOT" --cwd "$CALLER_CWD" <surface> ...`.
- Design authority lives in `nspl.py` plus Core Entry.

## Target Architecture

NSPL should have one Entry and many surfaces. The long-term command spine should move into `Core/NSPL/Entry`, while root `nspl.py` becomes a thin bootstrapper.

Proposed structure:

```text
Core/NSPL/Entry/
  __init__.py
  __main__.py
  entry.py
  context.py
  errors.py
  README.md

  Commands/
    __init__.py
    skill.py
    gui.py
    web.py

  Discovery/
    __init__.py
    descriptors.py
    skill_loader.py
    gui_loader.py
    web_loader.py
```

Responsibilities:

- `entry.py`: unified command parser, top-level routing, user-facing error handling, exit-code normalization.
- `context.py`: Entry context containing repo root, caller cwd, environment-derived roots, and surface-independent helpers.
- `errors.py`: Entry-level errors for invalid roots, invalid commands, duplicate descriptors, missing apps, and dependency guidance.
- `Commands/skill.py`: Skill surface adapter. Initially delegates to existing SkillCLI behavior; later owns Entry-native skill command handling where compatible.
- `Commands/gui.py`: GUI surface adapter. Initially delegates to existing GUICLI behavior; later owns Entry-native GUI command handling where compatible.
- `Commands/web.py`: Web surface command handling, descriptor discovery, and launch orchestration.
- `Discovery/descriptors.py`: shared descriptor scanning and validation primitives for `skill.json`, `gui.json`, and `web.json`.
- `Discovery/*_loader.py`: surface-specific descriptor contracts and module validation.

This structure is intentionally close to current SkillCLI/GUICLI patterns, but it prevents the long-term architecture from becoming three separate internal CLIs. If implementation shows that moving skill/gui loaders immediately is too risky, `Discovery/skill_loader.py` and `Discovery/gui_loader.py` can begin as thin imports/wrappers around the current loaders, then absorb shared descriptor code later.

## nspl.py Role

`nspl.py` should remain the repo-root executable gateway, but become thinner.

It should preserve:

- `--root`
- `--cwd`
- repo root validation
- caller cwd validation
- sys.path bootstrap
- `NSPL_CALLER_CWD`
- running Entry from repo root so ProjectRoot behavior remains stable

It should stop owning surface-specific dispatch where practical. The future flow should be:

1. `nspl.py` parses only bootstrap flags enough to identify repo root and caller cwd.
2. `nspl.py` bootstraps `sys.path`.
3. `nspl.py` constructs or passes Entry bootstrap context.
4. `nspl.py` delegates remaining argv to `Core.NSPL.Entry.entry.main`.
5. Entry routes to `skill`, `gui`, `web`, and future surfaces.

This keeps external wrappers stable because they already call `nspl.py --root ... --cwd ... <surface> ...`.

## Compatibility Strategy

Compatibility is a requirement, not a cleanup task.

- Do not delete `Core/NSPL/SkillCLI` or `Core/NSPL/GUICLI` in the first implementation pass.
- Do not break `python -m Core.NSPL.SkillCLI list`.
- Do not break `python -m Core.NSPL.SkillCLI skill <SkillName> [args...]`.
- Do not break `python -m Core.NSPL.GUICLI list`.
- Do not break `python -m Core.NSPL.GUICLI run <GuiName> [argv...]`.
- Do not break `skill.json` or `gui.json` contracts.
- Do not break `SKILLS_ROOT` or `GUI_ROOT` overrides.
- Do not break current no-import-on-list behavior.
- Do not break current one-module-import-on-run behavior.
- Do not break NodeCTX best-effort logging behavior.

Migration approach:

- Pass 1 can leave SkillCLI/GUICLI internals intact and have Entry delegate to them for behavior preservation.
- Later, SkillCLI/GUICLI module entrypoints can become compatibility shims that delegate to Entry command modules while preserving their current argv shapes and `prog`/usage behavior as much as practical.
- If exact help text changes would be risky, postpone shim conversion and keep direct SkillCLI/GUICLI implementations until Entry parity tests are strong.
- External wrappers should invoke the generic Entry surface shape through `nspl.py --root "$ROOT" --cwd "$CALLER_CWD" <surface> ...`.

## Unified Command Surface

Initial Entry surfaces:

- `python3 nspl.py skill ...`
- `python3 nspl.py gui ...`
- `python3 nspl.py web list`
- `python3 nspl.py web launch <WebAppName>`

Canonical Entry semantics:

- `python3 nspl.py skill list`
- `python3 nspl.py skill <SkillName> [args...]`
- `python3 nspl.py gui list`
- `python3 nspl.py gui run <GuiName> [argv...]`

Consider later, after compatibility is stable:

- `python3 nspl.py list skills`
- `python3 nspl.py list guis`
- `python3 nspl.py list web`

Those `list` aliases should not replace current surface-native list commands in the first pass. They can become convenience views once Entry owns enough shared discovery.

Possible future, not for this implementation:

- `python3 nspl.py app ...`

`app` could eventually represent bundled app workflows that compose skill/gui/web behavior, but adding it now would overbuild the Entry migration.

## Web Surface Design

Web should be an Entry surface, not a separate long-term CLI kingdom.

Recommended app location:

- `Web/<Domain>/<AppName>/web.json`
- `Web/<Domain>/<AppName>/app.py`
- optional `Web/<Domain>/<AppName>/templates/`
- optional `Web/<Domain>/<AppName>/static/`

Web app contract:

- Each app has `web.json`.
- Each app exposes `create_app(context)`.
- `create_app(context)` returns a FastAPI app.
- Web apps do not start Uvicorn.
- Entry `web launch` owns server launch, host/port binding, reload flags, and dependency errors.
- Web apps are shells/control surfaces. They should read/write through Core, NodeCTX, and/or Skills, not own hidden business logic or private state.

Web descriptor discovery should mirror existing discovery where reasonable:

- Default root: `Web/`.
- Override for tests/advanced use: `WEB_ROOT`.
- Scan recursively for `web.json`.
- Ignore empty/placeholder/broken descriptors during discovery.
- Require unique canonical `name`.
- Require `name`, `version`, and `description`.
- Default `entry` to `app.py`.
- Default `factory` to `create_app`.
- `web list` must not import app modules.
- `web launch` imports exactly one app module.

Minimal `web.json`:

```json
{
  "name": "RohTalk.Dashboard",
  "version": "0.1.0",
  "description": "Local RohTalk web dashboard",
  "entry": "app.py",
  "factory": "create_app"
}
```

Possible expanded descriptor:

```json
{
  "name": "Video.LookLabWeb",
  "version": "0.1.0",
  "description": "Mobile-friendly video workflow dashboard",
  "entry": "app.py",
  "factory": "create_app",
  "static_dir": "static",
  "templates_dir": "templates",
  "default_host": "127.0.0.1",
  "default_port": 8765,
  "requires": {
    "python": ["fastapi", "uvicorn", "jinja2"],
    "executables": ["ffmpeg"]
  }
}
```

Recommended launch flags:

- `--host <host>`, default `127.0.0.1`
- `--port <port>`, default `8765` or descriptor `default_port`
- `--reload`, dev-only
- `--log-level <level>`, default `info`

Example:

```text
python3 nspl.py web launch RohTalk.Dashboard --host 0.0.0.0 --port 8765
```

## Dependency Strategy

The repo currently does not appear to have a dependency manifest such as `pyproject.toml` or `requirements.txt`.

Recommendation:

- Prefer adding `pyproject.toml` now if the repo is ready to formalize dependency declarations.
- Keep base/core dependencies minimal.
- Put web dependencies behind an optional extra.
- Use optional extras rather than ambient undeclared imports.

Possible extras:

```toml
[project.optional-dependencies]
web = ["fastapi", "uvicorn[standard]", "jinja2"]
gui = ["PySide6"]
dev = ["pytest"]
```

Notes:

- `gui = ["PySide6"]` should be added only if it matches the existing GUI dependency reality and packaging stance.
- If `pyproject.toml` is judged too large for the immediate implementation, a temporary `requirements-web.txt` is acceptable, but the preferred direction should remain optional extras.
- Entry `web launch` should fail with clear actionable errors if required web dependencies are missing.
- A future helper such as `python3 nspl.py deps install web` could wrap installation guidance, but dependency installation is not required in the first Entry implementation.

Core portability language needs a precise update:

- Core/base remains stdlib-first.
- Entry itself should remain stdlib-first.
- The web surface has optional declared dependencies.
- Import FastAPI/Uvicorn only inside web launch paths so non-web commands stay usable without web extras installed.

## Portable Web Hosting Strategy

Web hosting is built into NSPL source, not outsourced:

- Running a web app starts a local Python web server from the repo/zip environment.
- This is not SaaS hosting.
- This is not a cloud dependency.
- This is not a hidden background daemon.
- The server is foreground and explicit while `nspl.py web launch ...` is running.
- Users can create their own service wrappers later, but that is outside the first Entry design.

Network behavior:

- Default host should be `127.0.0.1`.
- `127.0.0.1` is local-machine only.
- LAN access works when the user explicitly binds `--host 0.0.0.0` or a specific LAN IP, assuming firewall/network policy allows it.
- Tailscale access works if Tailscale is configured outside NSPL and the app binds to an address reachable from the tailnet.
- NSPL should not manage Tailscale.
- Entry can print clear bound URLs and a short reminder that firewall/Tailscale policy is external.

State behavior:

- Filesystem remains authoritative.
- Durable state lives in files, typically under `State/`.
- Web apps should use Core, NodeCTX, and/or Skill surfaces for durable reads/writes.
- No database, broker, cloud queue, or private in-memory server state should become source of truth.

## Staged Implementation Plan

### Pass 1: Entry Consolidation Skeleton

- Create `Core/NSPL/Entry`.
- Add Entry context, errors, parser, and command dispatch skeleton.
- Move `skill` and `gui` routing from `nspl.py` into Entry while preserving behavior.
- Keep `nspl.py` as a thin compatible bootstrapper.
- Keep SkillCLI/GUICLI code in place.
- Add tests proving `nspl.py skill ...` and `nspl.py gui ...` still behave as before.
- Add `Core/NSPL/Entry/README.md` and update root/Core docs to explain one Entry, many surfaces.

### Pass 2: Compatibility Shims

- Make `Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` delegate to Entry command modules where appropriate.
- Preserve `python -m Core.NSPL.SkillCLI ...` and `python -m Core.NSPL.GUICLI ...`.
- Preserve current list/run behavior, env overrides, descriptor contracts, user-facing errors, and exit codes.
- Keep existing tests passing before removing any duplicated command logic.

### Pass 3: Web Surface Discovery

- Add `Commands/web.py` under Entry.
- Add `Discovery/web_loader.py` and shared descriptor helpers if useful.
- Add `Web/<Domain>/<AppName>/` convention docs.
- Add `web list` and `web list --detailed`.
- Add tests for discovery, duplicate descriptors, invalid descriptors, placeholder descriptors, env root override, and no-import-on-list.

### Pass 4: Web Launch

- Add FastAPI/Uvicorn launch path under Entry web command.
- Add `EntryWebContext` or `WebContext` with repo root, caller cwd, app dir, descriptor metadata, and safe helper methods.
- Add missing dependency errors with installation guidance.
- Add `--host`, `--port`, `--reload`, and `--log-level`.
- Avoid long-running server tests where possible; test parser, dependency handling, factory loading, and launch-call wiring with fakes.

### Pass 5: First Minimal Web App

- Add `Web/NSPL/Status` or similar.
- Keep it read-only first.
- Use it to prove descriptor discovery, app factory loading, templates/static path resolution if used, and local serving from NSPL.
- Keep durable state reads routed through Core/NodeCTX.

### Pass 6: KanraQuest or RohTalk Web App

- Not part of the Entry implementation.
- Build only after the Entry web surface is proven.
- Use the established Web shell pattern rather than embedding workflow logic in the app server.

## Files Likely To Change Later

First implementation pass:

- `nspl.py`
- `Core/NSPL/Entry/__init__.py`
- `Core/NSPL/Entry/__main__.py`
- `Core/NSPL/Entry/entry.py`
- `Core/NSPL/Entry/context.py`
- `Core/NSPL/Entry/errors.py`
- `Core/NSPL/Entry/README.md`
- `Core/NSPL/Entry/Commands/__init__.py`
- `Core/NSPL/Entry/Commands/skill.py`
- `Core/NSPL/Entry/Commands/gui.py`
- Entry-focused tests
- `README.md`
- `Core/NSPL/README.md`

Later web passes:

- `Core/NSPL/Entry/Commands/web.py`
- `Core/NSPL/Entry/Discovery/__init__.py`
- `Core/NSPL/Entry/Discovery/descriptors.py`
- `Core/NSPL/Entry/Discovery/skill_loader.py`
- `Core/NSPL/Entry/Discovery/gui_loader.py`
- `Core/NSPL/Entry/Discovery/web_loader.py`
- dependency manifest, preferably `pyproject.toml`
- `Web/<Domain>/<AppName>/web.json`
- `Web/<Domain>/<AppName>/app.py`
- optional templates/static files

Compatibility shim pass:

- `Core/NSPL/SkillCLI/*`
- `Core/NSPL/GUICLI/*`

Those shim changes should happen only after Entry has tests strong enough to prove no behavior regression.

## Risks

- Over-refactoring too early could turn a web enablement task into a broad CLI rewrite.
- Existing SkillCLI/GUICLI behavior may regress through small differences in argparse, help text, exit codes, cwd, or environment handling.
- The repo could still end up with three internal CLIs if Entry only forwards forever and shared command ownership never moves inward.
- Moving too much discovery logic at once could destabilize known-good `skill.json` and `gui.json` behavior.
- Web apps may start owning workflow logic or hidden state instead of acting as shells over Core/NodeCTX/Skills.
- Binding web apps to LAN or Tailscale interfaces can expose local tools; localhost must remain the safe default.
- Optional web dependencies may appear to violate stdlib-first Core language unless Entry remains stdlib-first and web extras are documented as optional.
- Tests around cwd/root behavior can become brittle because `nspl.py`, Entry, ProjectRoot, and module invocations all care about process cwd.
- Uvicorn reload mode can alter import behavior; keep it optional and dev-only.

## Smallest First Implementation Pass

The smallest consolidation-safe pass is:

1. Add `Core/NSPL/Entry` with context, errors, parser, and `skill`/`gui` command modules.
2. Change `nspl.py` to bootstrap root/cwd exactly as today, then delegate command routing to Entry.
3. Have Entry `skill` call current SkillCLI implementation and Entry `gui` call current GUICLI implementation.
4. Add focused tests for existing `nspl.py skill ...` and `nspl.py gui ...` compatibility.
5. Add Entry docs describing one Entry, many surfaces.

Do not add Web launch in this pass. The first pass should prove consolidation without changing the behavior users already rely on.

## Acceptance Checklist

- No code files changed during this research revision.
- Plan now centers `Core/NSPL/Entry`.
- Plan avoids a long-term three-CLI architecture.
- SkillCLI/GUICLI compatibility path is defined.
- `nspl.py` thin-bootstrapper role is defined.
- Web surface is integrated through Entry.
- `skill.json` and `gui.json` compatibility is preserved.
- Existing `python -m Core.NSPL.SkillCLI` and `python -m Core.NSPL.GUICLI` compatibility is preserved.
- External wrappers are described as local conveniences, not internal architecture.
- Dependency strategy prefers `pyproject.toml` optional extras unless a strong reason is found not to.
- Filesystem remains truth.
- No database, broker, cloud dependency, or hidden daemon is introduced.
- Web launch remains explicit, local, and foreground.
- Default web bind remains localhost.
- First implementation pass is small, reversible, and testable.
