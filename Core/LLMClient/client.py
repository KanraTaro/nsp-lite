"""High‑level API for interacting with language model backends.

The :class:`LLMClient` class provides a single method,
``generate()``, which dispatches to a configured backend to obtain a
completion for a given prompt.  The default backend is ``ollama``.

Backends are implemented in the ``Core.LLMClient.backends`` package.
Future passes may introduce additional backends (e.g. OpenAI, Hugging
Face, etc.).  The backend name may be supplied at construction time.
"""

from __future__ import annotations
from typing import Optional, Any, Iterator
from .types import PostJSONCallable, StreamJSONCallable, LLMClientError, ChatResult, StreamEvent

class LLMClient:
    """Client for generating completions using different backends.

    Parameters:
        backend: the name of the backend to use; currently only
            ``"ollama"`` is supported
        http_post: optional dependency‑injected HTTP JSON helper.  When
            provided it will override the default helper used by the
            backend.  This is primarily intended for unit tests.
    """

    def __init__(
        self,
        *,
        backend: str = "ollama",
        http_post: Optional[PostJSONCallable] = None,
        http_stream: Optional[StreamJSONCallable] = None,
    ) -> None:
        """Create a new ``LLMClient``.

        Parameters:
            backend: The name of the backend to use.  Currently only
                ``"ollama"`` is supported.
            http_post: Optional dependency‑injected HTTP JSON helper.
                When provided it overrides the default helper used by
                the backend.  Primarily intended for unit tests.
            http_stream: Optional dependency‑injected streaming JSON
                helper.  When provided it overrides the default
                streaming helper used by the backend.  Primarily
                intended for unit tests.
        """
        self.backend = backend
        self.http_post = http_post
        self.http_stream = http_stream

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> str:
        """Generate a completion for ``prompt`` via the configured backend.

        The caller must supply a ``model`` unless their own wrapper
        specifies a default.  See ``Core/LLMClient/README.md`` for
        details on default behaviour.

        Returns the generated text or raises an exception from
        ``Core.LLMClient.types`` on error.
        """
        if self.backend != "ollama":
            # Future backends could be dispatched here
            raise LLMClientError(f"Unsupported backend: {self.backend}")

        # Import lazily to avoid unnecessary dependencies for other backends
        from .backends.ollama import generate as ollama_generate  # type: ignore

        return ollama_generate(
            prompt,
            model=model,
            host=host,
            timeout_s=timeout_s,
            http_post=self.http_post,
        )

    def chat(
        self,
        messages: Any,
        *,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout_s: Optional[float] = None,
        tools: Optional[list[Any]] = None,
        tool_choice: Optional[str] = None,
    ) -> ChatResult:
        """Send a chat conversation to the configured backend and return the final reply.

        Parameters:
            messages: A list of chat messages.  Entries may be plain
                dictionaries matching the backend schema or provider
                neutral ``Message`` instances.
            model: Name of the model to use.  Required unless your
                wrapper specifies a default.
            host: Base URL of the backend server.  Optional.  Defaults
                to the backend's default host when omitted.
            timeout_s: Optional timeout in seconds.
            tools: Optional list of available tool definitions.
            tool_choice: Optional hint indicating which tool should be
                forced.  Currently unused but reserved for future use.

        Returns:
            A provider‑neutral ``ChatResult`` describing the assistant's reply.

        Raises:
            ``LLMClientError`` or its subclasses when the operation
            fails.  See backend implementations for details.
        """
        if self.backend != "ollama":
            raise LLMClientError(f"Unsupported backend: {self.backend}")
        # Import lazily to avoid unnecessary dependencies for other backends
        from .backends.ollama import chat as ollama_chat  # type: ignore
        return ollama_chat(
            messages,
            model=model,
            host=host,
            timeout_s=timeout_s,
            tools=tools,
            tool_choice=tool_choice,
            http_post=self.http_post,
        )

    def chat_stream(
        self,
        messages: Any,
        *,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout_s: Optional[float] = None,
        tools: Optional[list[Any]] = None,
        tool_choice: Optional[str] = None,
    ) -> Iterator[StreamEvent]:
        """Stream a chat conversation via the configured backend.

        Parameters mirror those of :meth:`chat` with the addition that
        the return type is an iterator over ``StreamEvent`` objects.
        Each event represents either a text delta or a tool call.
        """
        if self.backend != "ollama":
            raise LLMClientError(f"Unsupported backend: {self.backend}")
        from .backends.ollama import chat_stream as ollama_chat_stream  # type: ignore
        return ollama_chat_stream(
            messages,
            model=model,
            host=host,
            timeout_s=timeout_s,
            tools=tools,
            tool_choice=tool_choice,
            http_post=self.http_post,
            http_stream=self.http_stream,
        )

    def chat_stream_collect(
        self,
        messages,
        *,
        model: Optional[str] = None,
        host: Optional[str] = None,
        timeout_s: Optional[float] = None,
        tools: Optional[list[Any]] = None,
        tool_choice: Optional[str] = None,
        on_text_delta: Optional[Any] = None,
    ):
        """Run a streaming chat call and collect it into a ChatResult.

        This consumes chat_stream(...) and returns a normalized ChatResult
        with:
        - full text
        - normalized tool_calls
        - assistant_message ready for history

        If ``on_text_delta`` is provided, it is called for each streamed
        text delta before the final result is assembled.
        """

        from .types import ChatResult, ToolCall

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        raw_events: list[Any] = []

        events = self.chat_stream(
            messages,
            model=model,
            host=host,
            timeout_s=timeout_s,
            tools=tools,
            tool_choice=tool_choice,
        )

        for event in events:
            raw_events.append(event.raw)

            if event.type == "text" and event.text_delta:
                text_parts.append(event.text_delta)
                if on_text_delta is not None:
                    on_text_delta(event.text_delta)

            elif event.type == "tool_call" and event.tool_call:
                tool_calls.append(event.tool_call)

        text = "".join(text_parts)

        if tool_calls:
            assistant_message = {
                "role": "assistant",
                "content": text if text else "",
                "tool_calls": [
                    {
                        "id": str(tc.id) if tc.id else "",
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in tool_calls
                ],
            }
        else:
            assistant_message = {
                "role": "assistant",
                "content": text,
            }

        return ChatResult(
            text=text,
            tool_calls=tool_calls,
            assistant_message=assistant_message,
            raw=raw_events,
        )
