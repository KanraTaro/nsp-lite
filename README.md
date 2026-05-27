# NSP Lite

NSP Lite is a local-first automation and app framework where the filesystem is
the source of truth.

Tasks, state, logs, app descriptors, and durable outputs live directly on disk.
That keeps the system inspectable with normal tools, portable across machines,
and resilient without requiring a database, broker, cloud service, or hidden
daemon.

The root `nspl.py` script is the repo bootstrap gateway. After it resolves the
repo root, caller cwd, and import path, command routing belongs to
`Core/NSPL/Entry`, the canonical NSPL command spine.

## Entry Surfaces

Entry currently exposes three surfaces:

- `skill`: one-shot action execution from `Skills/<Domain>/<SkillName>/`
- `gui`: desktop/native visual shells from `GUI/<Domain>/<GuiName>/`
- `web`: browser/mobile shells from `Web/<Domain>/<AppName>/`

Skills should stay thin and call reusable Core modules. GUI and Web apps are
control surfaces over Core, NodeCTX, and Skills; they should not become separate
sources of truth.

`Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` remain available as compatibility
entrypoints, but new architecture documentation should treat Entry as canonical.

## Quickstart

Requirements:

- Python 3.11+

From the repository root:

```bash
python nspl.py skill list
python nspl.py skill NSPL.Tools.Time.now --json
python nspl.py web list
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
```

Web support uses optional dependencies:

```bash
python -m pip install -e ".[web]"
```

`web launch` starts an explicit foreground local server. The safe default is
localhost. LAN or Tailscale access requires an explicit bind such as
`--host 0.0.0.0` or a reachable interface address, plus firewall/Tailscale
configuration outside NSPL.

## Current Validation

These commands exercise current discovery surfaces and the repository test
harness without clearing runtime state:

```bash
python nspl.py skill list
python nspl.py web list
python run_tests.py
```

`NSPL.Status`, launched in the Quickstart above, is the current reference Web
app for the Web-to-Entry-to-Skill path.

Known platform hardening work is tracked in
[`Docs/KNOWN_ISSUES.md`](Docs/KNOWN_ISSUES.md).

## Repository Layout

```text
Core/
  NSPL/
    Entry/       canonical command spine for skill, gui, and web surfaces
    SkillCLI/    compatibility entrypoint for the skill surface
    GUICLI/      compatibility entrypoint for the gui surface
    NodeCTX/     filesystem and JSONL logging utilities
  ChatOps/       filesystem-backed task queue primitives
  NodeCTX/       domain filesystem/logging utilities
  Video/         video-related reusable code
Skills/          one-shot action entrypoints discovered via skill.json
GUI/             desktop/native shells discovered via gui.json
Web/             browser/mobile shells discovered via web.json
Config/          optional presets and configuration
State/           generated runtime output, gitignored
Docs/            plans and developer guides
nspl.py          root bootstrap gateway
run_tests.py     test runner
```

## Domains

NSP Lite organizes most code by Domain. A Domain is a grouping label that can
appear across multiple roots:

- `Core/<Domain>/...` reusable logic and primitives
- `Skills/<Domain>/<SkillName>/...` runnable skill entrypoints
- `GUI/<Domain>/<GuiName>/...` optional desktop/native shells
- `Web/<Domain>/<AppName>/...` optional browser/mobile shells
- `Config/<Domain>/...` optional configuration and presets

Domains keep the repository navigable; they do not imply ownership hierarchy.

## Design Rules

- Filesystem artifacts remain authoritative.
- Core owns reusable logic, contracts, validation, and policy.
- Skills are thin one-shot action surfaces.
- GUI and Web apps are shells/control surfaces.
- Web apps expose `create_app(context)` and do not start Uvicorn themselves.
- Entry `web launch` owns local foreground server startup.
- Durable state belongs in files, usually under `State/`, not hidden browser,
  session, database, or server memory.

## License

MIT License.
