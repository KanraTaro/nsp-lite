# Entry Surfaces

Entry is the canonical NSPL command spine.

The root `nspl.py` script bootstraps the repository and delegates to
`Core/NSPL/Entry`. Entry owns command-surface routing.

## Current Surfaces

- `skill`: one-shot action execution
- `gui`: desktop/native shells
- `web`: browser/mobile shells

Examples:

```bash
python nspl.py skill list
python nspl.py gui list
python nspl.py web list
```

## Compatibility Shims

`Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` are compatibility packages. They
preserve existing module invocations and public command shape, but they are not
where new architecture behavior should be added.

Do not add new behavior to SkillCLI/GUICLI unless the change is strictly about
maintaining compatibility.

## Future Surfaces

Future surfaces may be added under `Core/NSPL/Entry`. They should follow the
same pattern:

- route from `nspl.py` through Entry
- keep reusable logic in Core
- keep durable truth in filesystem artifacts
- avoid hidden databases, brokers, or background services as source of truth

External wrappers such as `nspl-skill` and `nspl-gui` are local conveniences.
They are not internal architecture; their stable target is the repo `nspl.py`
gateway.
