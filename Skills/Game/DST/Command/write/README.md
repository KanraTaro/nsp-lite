# Game.DST.Command.write

`Game.DST.Command.write` is the low-level safe command writer for RohBridge DST
commands. Existing calls without transport flags still write the legacy command
slot, `roh_dst_command.json`.

Transport flags:

- `--queue` appends to `roh_dst_command_queue.json`.
- `--command-id <id>` supplies a caller-controlled command id.
- `--wait-result` waits for `roh_dst_command_result.json` to contain the same
  `command_id`.
- `--result-timeout <seconds>` and `--result-interval <seconds>` control result
  polling.

Use `--queue` for normal RohBridge command delivery when command ordering
matters. Add `--wait-result` when the caller needs acceptance, rejection, or
diagnostic details from RohBridge. The wrapper skills expose the same transport
flags while keeping the payload-building logic thin.

