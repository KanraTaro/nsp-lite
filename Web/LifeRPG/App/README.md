# LifeRPG.App

Local FastAPI shell for the LifeRPG MVP slice.

Launch:

```bash
python nspl.py web launch LifeRPG.App --host 127.0.0.1 --port 8770
```

The app is discovered from `Web/LifeRPG/App/web.json` and exposes
`create_app(context)`. Routes call LifeRPG skills through `WebContext.run_skill`
using flattened skill args such as `["LifeRPG.Inbox.Add", "--text", "..."]`.

Pass 1 uses HTMX from a CDN for partial swaps. The routes still perform durable
server-side actions through SkillCLI. State defaults to
`State/main/Global/LifeRPG/...`.

Deferred: live RohTalk integration, ClickUp, node targeting, conflict strategy,
browser notifications, production auth, background daemons, and advanced combat.
