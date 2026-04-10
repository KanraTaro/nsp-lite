# RohTalk Skills

This directory exposes the RohTalk core via user-facing skills.

Each skill is discovered and invoked through SkillCLI and operates
against the same RohTalk conversation store.

Run skills through the dispatcher:

python -m Core.NSPL.SkillCLI list
python -m Core.NSPL.SkillCLI skill RohTalk.oneshot -- "Ask me a question"

---

## Available skills

### RohTalk.oneshot

Execute a single prompt without creating a long-lived chat session.

The prompt is stored as a conversation with kind `oneshot` so that
record keeping still works, but oneshots are hidden from the default
conversation list.

Usage:

python -m Core.NSPL.SkillCLI skill RohTalk.oneshot [--model MODEL] [--host URL] -- <your prompt>

---

### RohTalk.start

Start a new persistent conversation and run the first model turn.

If `--title` is omitted, RohTalk derives a title automatically from the
first user message.

Usage:

python -m Core.NSPL.SkillCLI skill RohTalk.start [--title TITLE] [--model MODEL] [--host URL] -- <your prompt>

Output:

- conversation_id
- title
- assistant reply

---

### RohTalk.chat

Append a message to an existing conversation and run one model turn.

Usage:

python -m Core.NSPL.SkillCLI skill RohTalk.chat <conversation_id> [--model MODEL] [--host URL] -- <your message>

Arguments:

- `<conversation_id>` - existing conversation id
- `--model` - optional override
- `--host` - optional override

---

### RohTalk.show_conversation

Display a stored conversation in readable form.

You can pass either:

- full conversation id
- numeric index from list_conversations

Usage:

python -m Core.NSPL.SkillCLI skill RohTalk.show_conversation <conversation_id_or_index>

---

### RohTalk.list_conversations

List stored conversations.

By default oneshot conversations are hidden.

Each line prints:

[index] title | short_id | updated_timestamp

Usage:

python -m Core.NSPL.SkillCLI skill RohTalk.list_conversations [--include-oneshots]

The numeric index can be used with show_conversation.

---

## Suggested CLI flow

Start a conversation:

python -m Core.NSPL.SkillCLI skill RohTalk.start --title "DST Run" -- "We just entered winter, what should I do?"

List conversations:

python -m Core.NSPL.SkillCLI skill RohTalk.list_conversations

Show one:

python -m Core.NSPL.SkillCLI skill RohTalk.show_conversation 0

Continue it:

python -m Core.NSPL.SkillCLI skill RohTalk.chat <conversation_id> -- "What should I gather first?"

---

## Where data is written

State/<Instance>/<NodeTag>/RohTalk/Workflow/Conversations/

Override context using:

--instance
--node
--global
