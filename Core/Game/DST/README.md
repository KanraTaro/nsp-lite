# Core.Game.DST

Core DST code owns reusable RohBridge contracts: path discovery, command
validation, command queue JSON, legacy command writes, and result polling.
SkillCLI wrappers should call these helpers instead of reimplementing file
transport logic.

Resolved RohBridge paths include:

- `snapshot_path`
- `command_path`
- `command_queue_path`
- `command_result_path`
- `save_dir`
- `source`

Legacy writes target `roh_dst_command.json`. Queue writes append to
`roh_dst_command_queue.json` using schema `dst.v0.4.command_queue`. Result
polling reads `roh_dst_command_result.json` and only treats a result as matched
when `command_id` equals the command being tracked.

