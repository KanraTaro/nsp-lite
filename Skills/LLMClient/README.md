# Skills/LLMClient

Skills/LLMClient are user-facing entrypoints for talking to a locally running LLM via **Core/LLMClient**.

These skills do not implement HTTP, streaming, or parsing themselves. They are thin wrappers that:

- parse CLI flags
- construct minimal request inputs
- call `Core.LLMClient.client.LLMClient`
- print user-facing output
- return a process exit code

If you want to change protocol behavior, error mapping, or backend behavior, do it in **Core/LLMClient**.

---

## Skills

### LLMClient.ollama_generate

Send a plain prompt to Ollama and print the full generated response.

Flags:
- `--host <url>` optional (default: http://localhost:11434)
- `--model <name>` required
- `--timeout <sec>` optional

Prompt:
- all remaining tokens are joined into a single prompt string
- use `--` if your prompt begins with a dash

Example:

python nspl.py skill LLMClient.ollama_generate \
  --instance main \
  --model qwen3:0.6b \
  -- "Say hi in one sentence."

Exit codes:
- `0` success
- `1` request/model/client error
- (skill may return other non-zero codes if Core raises unexpected errors)

---

### LLMClient.ollama_chat

Send a minimal chat conversation (one user message) and print the final assistant reply.

Flags:
- `--host <url>` optional (default: http://localhost:11434)
- `--model <name>` required
- `--timeout <sec>` optional

Prompt:
- all remaining tokens are joined into a single user message
- use `--` if your message begins with a dash

Example:

python nspl.py skill LLMClient.ollama_chat \
  --instance main \
  --model qwen3:0.6b \
  -- "You are a helpful assistant. Reply with exactly 10 words."

Exit codes:
- `0` success
- `1` request/model/client error
- `2` missing required args (model or prompt)

---

### LLMClient.ollama_stream

Stream a minimal chat request and print the response incrementally.

Notes:
- This prints text deltas as they arrive.
- Tool calls are not executed. If present, they are printed as `[tool_call] ...` notes.

Flags:
- `--host <url>` optional (default: http://localhost:11434)
- `--model <name>` required
- `--timeout <sec>` optional

Example:

python nspl.py skill LLMClient.ollama_stream \
  --instance main \
  --model qwen3:0.6b \
  -- "Write a short poem, streaming is fine."

Exit codes:
- `0` success
- `1` request/model/client error
- `2` missing required args (model or prompt)

---

## Relationship to Core/LLMClient

- **Core/LLMClient** owns protocol behavior, backend selection, HTTP concerns, and error mapping.
- **Skills/LLMClient** exists so users/workers can invoke LLM calls through SkillCLI with a stable CLI surface.

---

## Quick sanity checks

Assuming Ollama is running at the default host and the model is pulled:

ollama pull qwen3:0.6b

python nspl.py skill LLMClient.ollama_generate --instance main --model qwen3:0.6b -- "Hello"

python nspl.py skill LLMClient.ollama_chat --instance main --model qwen3:0.6b -- "Hello"

python nspl.py skill LLMClient.ollama_stream --instance main --model qwen3:0.6b -- "Hello"

