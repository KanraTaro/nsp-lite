# Testing And Validation

Validation should match the risk of the change.

## Focused Tests

Run focused tests for touched modules first.

```bash
python -m unittest Web.LifeRPG.App.Tests.test_app
python -m unittest Core.RohTalk.Tests.test_rohtalk
python -m unittest Core.NSPL.NodeCTX.Tests.test_node_ctx
```

Compile changed Python files:

```bash
python -m py_compile <changed-python-files>
```

## Full Harness

Run the repo harness after behavior changes and for broad cleanup passes:

```bash
python run_tests.py
```

## Command Surface Checks

```bash
python nspl.py skill list
python nspl.py web list
```

These catch discovery and descriptor regressions.

## Manual Web Smoke

For Web apps:

```bash
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
```

Then verify the actual user flow in a browser or local HTTP smoke:

- default screen is usable
- add/edit/start/complete actions work
- related panels update
- mobile layout is not broken
- no panel nesting

## Diff Hygiene

```bash
git diff --check
```

Report skipped validation honestly.

## UX Tests

UX testing cannot be replaced by route-200 tests. Assert visible outcomes: compact dashboards, collapsed edit controls, enum selects, meaningful empty states, and coherent HTMX updates.
