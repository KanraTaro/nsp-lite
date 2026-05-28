# LifeRPG Skills

LifeRPG skills are thin SkillCLI wrappers around `Core/LifeRPG`.

Use the flattened Entry command shape:

```bash
python nspl.py skill LifeRPG.Inbox.Add --text "fix dad page, laundry"
python nspl.py skill LifeRPG.Inbox.Sort
python nspl.py skill LifeRPG.Mission.Status
```

State defaults to the Global MVP scope: `State/main/Global/LifeRPG/...`.
