# Game.DST Skills

DST skills are thin SkillCLI wrappers around RohBridge command JSON files.
Reusable command validation and payload builders live in `Core/Game/DST`.

Command-writing skills keep legacy behavior by default: they write one command
object to `roh_dst_command.json`. Pass `--queue` to append the command to
`roh_dst_command_queue.json` instead. Queued commands receive a `command_id`
when one is not provided, which lets wrappers match RohBridge acknowledgments
from `roh_dst_command_result.json`.

Pass `--wait-result` when a caller needs RohBridge acceptance or rejection
details. The JSON response includes `queued`, `command`, `command_id`,
`result_path`, and `bridge_result` when a matching result arrives. On timeout,
the command write is still reported with `ok:false` and `reason:"result_timeout"`.
Because RohBridge exposes only the latest result file, matching by `command_id`
is important.

The `dst_director` RohTalk toolkit exposes wrapper tools for snapshot reads,
announcements, objectives, chaos tier changes, allowlisted supply/enemy spawns,
allowlisted frog-rain events, and RohBridge-tracked spawn cleanup. It does not
expose raw `Game.DST.Command.write` by default. Model-facing command tools use
queued writes and wait for result acknowledgments internally, without exposing
transport flags in the tool schemas, so AutoRoh can see RohBridge rejection
reasons in tool results.

RohBridge queue writes are file based and not atomic against simultaneous
writers. Longer multi-command director sequences may still need a higher-level
batch helper later.
