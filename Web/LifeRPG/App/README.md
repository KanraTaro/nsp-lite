# LifeRPG.App

Local FastAPI shell for the LifeRPG MVP slice.

Launch:

```bash
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
```

The app is discovered from `Web/LifeRPG/App/web.json` and exposes
`create_app(context)`. Routes call LifeRPG skills through `WebContext.run_skill`
using flattened skill args such as `["LifeRPG.Inbox.Add", "--text", "..."]`.

The app uses HTMX from a CDN for partial swaps. Full panel partials use stable
outer IDs and `hx-swap="outerHTML"` so management actions replace panels instead
of nesting them. Routes still perform durable server-side actions through
SkillCLI. State defaults to
`State/main/Global/LifeRPG/...`.

Pass 2A exposes basic app management for inbox items, quests, habits, events,
quest session notes, and settings. The Board stays a compact command center:
management pages use progressive disclosure for create/edit controls, select
inputs for app choice fields, and HTMX out-of-band swaps for related panels.
The app remains server-rendered and does not require frontend build tooling.

Deferred: live RohTalk integration, ClickUp, node targeting, conflict strategy,
browser notifications, production auth, background daemons, and advanced combat.
