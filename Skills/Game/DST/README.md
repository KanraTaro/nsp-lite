# Game.DST Skills

DST skills are thin SkillCLI wrappers around RohBridge command JSON files.
Reusable command validation and payload builders live in `Core/Game/DST`.

The `dst_director` RohTalk toolkit exposes wrapper tools for snapshot reads,
announcements, objectives, chaos tier changes, allowlisted supply/enemy spawns,
allowlisted frog-rain events, and RohBridge-tracked spawn cleanup. It does not
expose raw `Game.DST.Command.write` by default.
