# RohTalk Skills

This directory exposes the RohTalk core via three user‑facing skills.
Each skill is discovered and invoked through the standard
``SkillCLI`` mechanism and operates against the RohTalk conversation
store.  Skills must be run via the dispatcher:

```sh
python -m Core.NSPL.SkillCLI list
python -m Core.NSPL.SkillCLI skill RohTalk.oneshot -- "Ask me a question"
```

## Available skills

### `RohTalk.oneshot`

Execute a single prompt without creating a long‑lived chat session.
The prompt is stored as a conversation with kind `oneshot` so that
record keeping and auditing still work, but oneshots are hidden from
the default conversation list.  The skill prints only the assistant’s
reply to standard output.

**Usage:**

```sh
python -m Core.NSPL.SkillCLI skill RohTalk.oneshot [--model MODEL] [--host URL] -- <your prompt>
```

Options:

* `--model` – Override the default model (otherwise uses the value from the RohTalk config)
* `--host` – Override the backend URL (otherwise uses the value from the RohTalk config)

All arguments after `--` are joined into a single prompt.

### `RohTalk.chat`

Append a message to an existing conversation and run one model turn.  The
conversation identifier must be supplied.  If the conversation does
not exist, the skill exits with a non‑zero status and prints an
error.

**Usage:**

```sh
python -m Core.NSPL.SkillCLI skill RohTalk.chat <conversation_id> [--model MODEL] [--host URL] -- <your message>
```

Arguments:

* `<conversation_id>` – Identifier of the existing conversation to append to
* `--model` – Optional model override
* `--host` – Optional backend URL override

All tokens after `--` are joined into the user message.

### `RohTalk.list_conversations`

List stored conversations.  By default oneshot conversations are
omitted.  Each line of output contains the conversation id followed
by the last updated timestamp.  Ordering is from oldest to newest.

**Usage:**

```sh
python -m Core.NSPL.SkillCLI skill RohTalk.list_conversations [--include-oneshots]
```

Options:

* `--include-oneshots` – Include oneshot conversations in the list.

## Where data is written

All skills operate relative to the current SkillCLI context.  By
default, data is written under:

```
State/<Instance>/<NodeTag>/Workflow/RohTalk/Conversations/
```

The instance id and node tag can be overridden with the standard
SkillCLI flags `--instance` and `--node`.  To operate in global
scope, pass `--global`.  See the `SkillCLI` documentation for
details.