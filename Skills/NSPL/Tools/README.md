# Skills/NSPL/Tools

Tools are intentionally boring utility skills used to validate the NSPL runtime spine.

They exist for two reasons:

1) **Pipeline verification**
   You need at least one skill that always succeeds (and is easy to eyeball),
   and at least one skill that always fails (to verify error paths).

2) **Stable integration targets**
   ChatOps and other orchestrators can call these without pulling in app-specific logic.

These skills are executed through the Entry skill surface like everything else.

---

## Tool skills

### NSPL.Tools.Echo.echo

Echo a message back to stdout.

- Accepts any number of message tokens.
- Joins them with spaces and prints the result.
- Returns exit code `0`.

Example:

python nspl.py skill skill NSPL.Tools.Echo.echo \
  --instance main \
  -- hello world

---

### NSPL.Tools.Time.now

Print the current time to stdout. With `--json`, it emits a compact JSON
payload with UTC time, local time, timezone, offset, date, and display fields.

- Optional `--timezone` / `--tz` accepts an IANA timezone name.
- Returns exit code `0`.

Example:

python nspl.py skill skill NSPL.Tools.Time.now \
  --timezone America/New_York \
  --json

---

### NSPL.Tools.TestFail.fail

A deliberate failure skill for testing failure paths.

- Optional `--message` prints to stdout first.
- Always returns exit code `1`.

Example:

python nspl.py skill skill NSPL.Tools.TestFail.fail \
  --instance main \
  --message "this should fail"

---

## Recommended usage

Before trusting any “real” automation, validate:

1) Success path:
   - enqueue `NSPL.Tools.Echo.echo` through ChatOps
   - confirm Done/ result and stdout

2) Failure path:
   - enqueue `NSPL.Tools.TestFail.fail` through ChatOps
   - confirm Failed/ result and stderr/exit_code

Keep these tools permanently. They are your smoke alarm.
