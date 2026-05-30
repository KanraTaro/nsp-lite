# NSPL Developer Docs

These are practical contributor guides. They supplement `AGENTS.md`, `00_AGENT_HANDOFF.md`, and the agent docs under `Docs/Agents/`.

## Guides

- `Create-Skill.md`: create a SkillCLI entrypoint.
- `Create-Web-App.md`: create a Web app launched through Entry.
- `Entry-Surfaces.md`: understand canonical command surfaces.
- `NodeCTX-State-Guide.md`: use runtime state safely.
- `Web-App-UX-Patterns.md`: build HTMX apps without CRUD-wall UX.
- `RohTalk-Integration-Guide.md`: treat RohTalk as the shared operator runtime.
- `Testing-And-Validation.md`: run focused and full validation.
- `Agent-Pass-Reports.md`: write useful pass reports.

## Rules Of Thumb

- Core owns reusable behavior.
- Skills are thin executable actions.
- Web/GUI are control surfaces.
- NodeCTX owns durable runtime state.
- Docs should be public/contributor safe.
