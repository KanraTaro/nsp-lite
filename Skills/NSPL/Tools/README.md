# Skills/NSPL/Tools

Tools are intentionally boring “utility” skills used to validate the NSPL runtime spine.

They exist for two reasons:

1) **Pipeline verification**
   You need at least one skill that always succeeds (and is easy to eyeball),
   and at least one skill that always fails (to verify error paths).

2) **Stable integration targets**
   ChatOps and other orchestrators can call these without pulling in app-specific logic.

These skills are executed via **SkillCLI** like everything else.

---

## Tool skills

### Tools.Echo.echo

Echo a message back to stdout.

- Accepts any number of message tokens.
- Joins them with spaces and prints the result.
- Returns exit code `0`.

Example:

python -m Core.NSPL.SkillCLI skill Tools.Echo.echo \
  --instance main \
  -- hello world

---

### Tools.Time.now

Print the current UTC timestamp (ISO 8601, `Z` suffix) to stdout.

- No args.
- Returns exit code `0`.

Example:

python -m Core.NSPL.SkillCLI skill Tools.Time.now \
  --instance main

---

### Tools.TestFail.fail

A deliberate failure skill for testing failure paths.

- Optional `--message` prints to stdout first.
- Always returns exit code `1`.

Example:

python -m Core.NSPL.SkillCLI skill Tools.TestFail.fail \
  --instance main \
  --message "this should fail"

---

## Recommended usage

Before trusting any “real” automation, validate:

1) Success path:
   - enqueue `Tools.Echo.echo` through ChatOps
   - confirm Done/ result and stdout

2) Failure path:
   - enqueue `Tools.TestFail.fail` through ChatOps
   - confirm Failed/ result and stderr/exit_code

Keep these tools permanently. They are your smoke alarm.

