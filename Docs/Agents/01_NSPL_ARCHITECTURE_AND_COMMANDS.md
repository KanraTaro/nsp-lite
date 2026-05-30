# NSPL Architecture and Commands

## Canonical Repository Shape

```text
Config/<Domain>/                 Optional repo-local config and presets
Core/<Domain>/                   Reusable logic, contracts, services, tests
Skills/<Domain>/<Skill>/         Thin executable SkillCLI entrypoints
Web/<Domain>/<App>/              Browser/mobile apps launched by Entry
GUI/<Domain>/<Gui>/              Desktop/native apps launched by Entry
Docs/                            Plans, developer docs, agent docs, reports
State/                           Runtime state, generated, not source
nspl.py                          Root Entry gateway
run_tests.py                     Repo test runner
```

## Entry Gateway

`nspl.py` is the root gateway. It resolves the repo root, preserves caller cwd context, puts the repo root on `sys.path`, exports `NSPL_CALLER_CWD`, and dispatches to Entry surfaces from the repo root.

Canonical Entry surfaces:

- `skill`: one-shot action execution
- `gui`: desktop/native visual shells
- `web`: browser/mobile shells

## Canonical Commands

### Web

```bash
python nspl.py web list
python nspl.py web launch NSPL.Status --host 127.0.0.1 --port 8765
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
```

Web apps must expose:

```python
def create_app(context):
    ...
```

Web apps must not start Uvicorn directly. Entry owns foreground server startup.

### Skills

Canonical skill syntax is flattened:

```bash
python nspl.py skill list
python nspl.py skill <Skill.Name> [args...]
```

Examples:

```bash
python nspl.py skill NSPL.Tools.Time.now --json
python nspl.py skill NSPL.Tools.Echo.echo -- "hello"
python nspl.py skill RohTalk.start -- "Hello"
python nspl.py skill RohTalk.chat 0 -- "Continue this thought"
python nspl.py skill LifeRPG.Inbox.Add --text "fix web page"
python nspl.py skill LifeRPG.Inbox.Sort --json
```

Do not use old doubled syntax:

```bash
python nspl.py skill <leading-skill-token> <Skill.Name>
nspl-skill <leading-skill-token> <Skill.Name>
```

### GUI

```bash
python nspl.py gui list
python nspl.py gui run Video.LookLab
```

Historical compatibility paths may exist, but Entry is canonical.

## WebContext Skill Invocation

Web apps can call Skills through `WebContext.run_skill(...)`.

Use flattened args:

```python
context.run_skill(["LifeRPG.Inbox.Add", "--text", "fix web page"])
```

Do not pass a leading `skill` token:

```python
context.run_skill(["skill", "LifeRPG.Inbox.Add", "--text", "fix web page"])
```

## NodeCTX State Contract

NodeCTX routes durable state through this canonical layout:

```text
State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/
```

Important terms:

- `InstanceId`: runtime instance, usually `main` for MVPs.
- `Scope`: `Global` or a node tag such as `Workstation`.
- `Domain`: product/system domain, such as `LifeRPG`, `RohTalk`, `ChatOps`.
- `Bucket`: normalized state area such as `Data`, `Workflow`, `Logs`, `Config`, `Reflections`.
- `Subpath`: domain-owned structure.

For LifeRPG MVP, use:

```text
State/main/Global/LifeRPG/...
```

For durable writes, use NodeCTX/store helpers. Avoid direct ad-hoc path construction.

## Common State Buckets

```text
Config/       App/user config and profile settings
Data/         Durable objects: quests, inbox items, habits, events, agents
Workflow/     Runtime state: active sessions, queues, proposals, ledgers
Logs/         JSONL event logs and audit trails
Reflections/  Longer summaries/reflection artifacts
```

## Skill Structure

A Skill normally contains:

```text
Skills/<Domain>/<SkillName>/
├── skill.json
├── skill.py
└── Tests/          optional but preferred for non-trivial skills
```

`skill.json` declares the canonical skill name.

`skill.py` should expose:

```python
def build_parser(parser):
    ...

def run(args, ctx) -> int:
    ...
```

Skills should support `ctx.json` where practical.

## Web App Structure

A Web app normally contains:

```text
Web/<Domain>/<App>/
├── web.json
├── app.py
├── views.py / view_models.py / ui_choices.py as needed
├── templates/
├── static/
├── Tests/
└── README.md
```

`web.json` names the app and its factory.

`app.py` exposes `create_app(context)`.

## HTMX App Rules

When using HTMX:

- Full-panel partials should have stable outer IDs.
- Full-panel replacements should use `hx-swap="outerHTML"`.
- Avoid `hx-target="closest section"` for full-panel returns.
- Use out-of-band swaps when one action affects multiple panels.
- Tests should verify user-visible state, not just panel IDs.

## Validation Commands

Typical focused validation:

```bash
python -m py_compile <changed python files>
python -m unittest <focused test module>
python run_tests.py
python nspl.py skill list
python nspl.py web list
git diff --check
```

Manual Web smoke:

```bash
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
```

Then test in browser.

## Exclusions for Repo Context Zips

When creating context zips for agents, exclude:

```text
State/
.git/
__pycache__/
.pytest_cache/
*.egg-info/
*.pyc
.venv/
node_modules/
```

Mockups and docs can stay unless the package is too large.
