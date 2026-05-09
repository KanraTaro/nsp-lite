# AutoRoh Core

AutoRoh is a generic observed, tool-capable loop. It is not DST-specific; game or workflow-specific behavior belongs in profiles and toolkits.

## Module Boundaries

- `state.py`: durable loop state.
- `notes.py`: human note scanning.
- `observations.py`: observation tool execution and signature hashing.
- `tool_events.py`: tool call/result event shaping and action signatures.
- `policy.py`: advisory cooldown text.
- `prompts.py`: tick prompt construction.
- `profiles.py`: toolkit/workflow-specific behavior, rules, and cooldowns.
- `director_packs.py`: generic loading and prompt rendering for domain content packs.

`Skills/AutoRoh/run` is the SkillCLI orchestration entrypoint. It wires the loop together, resolves the selected profile, and delegates reusable behavior to Core modules.

## Profiles

`dst_director` is the first concrete profile/toolkit pairing. It carries DST-specific prompt guidance, command cooldowns, and a small Director Pack outside the generic AutoRoh loop.

The DST director profile uses a live action budget: passive ticks allow one successful DST action tool, while ticks with an explicit human note may allow up to three successful DST action tools for short multi-step instructions. The generic loop reads this from the profile; `max_steps` still bounds runaway tool loops.

Director Packs provide domain content such as style guidance, examples, safe prefab lists, objective templates, and constraints. They do not execute tools, own loop behavior, or contain Python logic. DST pack content lives under `Core/Game/DST/DirectorPacks`, mirroring the `Skills/Game/DST` domain path.

Future workflows such as `web_worker` or `research_worker` should add profiles and toolkits instead of hardcoding workflow behavior into `AutoRoh.run`.
