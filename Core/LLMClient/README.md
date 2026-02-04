# LLMClient Core Module

The **LLMClient** module provides a thin, backend‐agnostic interface for
sending plain prompts to a locally running LLM and returning the
generated text.  It currently ships with a single backend implementation
for [Ollama](https://ollama.com), a local model runner that exposes a
simple HTTP API.  Future passes may add additional backends or richer
chat/session support, but the goal of this module in Pass 1 is to
demonstrate a working end‑to‑end integration with Ollama.

## Quick start

```sh
# from the repository root, list available skills
python -m Core.NSPL.SkillCLI list

# run the ollama_generate skill against a running Ollama instance
python -m Core.NSPL.SkillCLI skill LLMClient.ollama_generate \
  --host http://localhost:11434 \
  --model llama3.2 \
  -- "Hello, world"
```

The skill accepts a positional prompt (any remaining tokens after
`--` are joined with spaces), and two optional flags:

- `--host`: Override the base URL of the Ollama server.  The default
  host is `http://localhost:11434`.  If your Ollama instance listens on
  another port or hostname, supply it here.
- `--model`: Specify the model name to generate against.  Ollama will
  only serve responses for models that have been pulled locally (e.g.
  via `ollama pull llama3.2`).  There is no repo‑wide default model;
  if omitted, you must supply a model when calling the skill or when
  using the `Core.LLMClient.client.LLMClient` API directly.  You can
  set your own preferred default in your own code by passing a
  `model` argument to `generate()`.
- `--timeout`: Optional timeout in seconds for the request.  If the
  request takes longer than this number of seconds the call will be
  aborted and a timeout error will be raised.

## API overview

At the core of this module is the `LLMClient` class defined in
`Core/LLMClient/client.py`.  It exposes a single method:

```python
LLMClient.generate(prompt: str, *, model: str | None = None,
                   host: str | None = None,
                   timeout_s: float | None = None) -> str
```

The method accepts a plain text prompt and optional `model`, `host`
and `timeout_s` parameters.  It returns the raw text of the model’s
response.  If an error occurs the method raises one of the custom
exceptions defined in `Core/LLMClient/types.py`:

- `ConnectionError`: the Ollama server is unreachable (e.g. it is not
  running or the host is incorrect).
- `ModelNotFoundError`: the specified model has not been pulled locally.
- `TimeoutError`: the request exceeded the provided timeout.
- `HTTPStatusError`: the Ollama server returned a non‑200 status code.
- `LLMClientError`: a catch‑all for other unexpected conditions.

Consumers of this API should catch these exceptions and map them to
user‑facing messages.  The included skill does this for you.

## Implementation notes

- **Backend selection** – Pass 1 only implements the Ollama backend.
  Additional backends can be added under `Core/LLMClient/backends/`
  with their own `generate()` functions.  The `LLMClient` class will
  dispatch based on the configured backend name.
- **Default host** – The default host is `http://localhost:11434`,
  which matches the default for a vanilla Ollama installation.  If
  your Ollama server is bound to a different address you must pass
  `--host`.
- **Model default** – There is deliberately no hard‑coded default
  model.  Models vary widely in size and capability, and requiring an
  explicit `--model` argument avoids accidentally loading an enormous
  model.  If your workflow prefers a default you can wrap
  `LLMClient.generate()` in your own helper that supplies one.

## Error handling

Errors raised from `LLMClient.generate()` are surfaced as custom
exceptions.  When executing via the `LLMClient.ollama_generate` skill
these exceptions are caught and printed as concise messages.  Examples
of user‑visible errors include:

- *Ollama not running or host unreachable* – the client could not
  connect to the Ollama server.  Check that the service is running and
  the `--host` URL is correct.
- *Model not available locally; run: `ollama pull <model>`* – the
  specified model has not been pulled.  Use `ollama pull` to download
  it first.
- *Request timed out after X seconds* – the call to the server took
  longer than the specified timeout.
- *Ollama server returned status NNN: …* – the server returned a
  non‑200 HTTP status.  The message will include the status code and a
  snippet of the response body to aid debugging.

The unit tests in `Core/LLMClient/Tests/test_ollama_backend.py` cover
request building, response parsing and error mapping to ensure the
module behaves predictably without requiring a running Ollama during
testing.