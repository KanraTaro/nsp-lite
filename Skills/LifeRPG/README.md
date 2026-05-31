# LifeRPG Skills

LifeRPG skills are thin SkillCLI wrappers around `Core/LifeRPG`.

Use the flattened Entry command shape:

```bash
python nspl.py skill LifeRPG.Inbox.Add --text "fix dad page, laundry"
python nspl.py skill LifeRPG.Inbox.Sort
python nspl.py skill LifeRPG.Quest.Create --title "Draft proposal" --project "Example Project"
python nspl.py skill LifeRPG.Quest.Detail --quest-id "<quest_id>"
python nspl.py skill LifeRPG.Habit.Create --title "Drink water"
python nspl.py skill LifeRPG.Event.Create --title "Daily reset" --starts-at "2026-05-28T06:00:00"
python nspl.py skill LifeRPG.Settings.Update --display-name "Operator"
python nspl.py skill LifeRPG.Mission.Status
```

State defaults to the Global MVP scope: `State/main/Global/LifeRPG/...`.

Quest and sorted inbox metadata now distinguish `project` from `category`.
Category describes the kind of work; project describes the larger effort.
