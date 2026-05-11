"""Unit tests for the LLMClient Ollama streaming chat backend.

These tests verify that the streaming logic correctly parses NDJSON
chunks into provider-neutral ``StreamEvent`` objects and maps errors
into the appropriate exception types defined in
``Core.LLMClient.types``. The streaming layer is mocked so that no
real network requests are made.
"""

from __future__ import annotations

import socket
import unittest
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple
from urllib import error as urlerror

from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import (
    ConnectionError,
    ModelNotFoundError,
    TimeoutError,
    HTTPStatusError,
    LLMClientError,
)
from Core.LLMClient.http_json import HTTPError as JSONHTTPError


class DummyStream:
    """Helper class to simulate a streaming JSON POST.

    ``chunks``: an iterable of JSON-serialisable objects or raw JSON
        strings to yield to the client.
    ``exception``: optional exception to raise instead of returning a
        normal iterator. When set, no chunks are yielded and the
        exception is raised immediately.
    The callable records calls so that tests can inspect the URL and
    payload used by the client.
    """

    def __init__(
        self, chunks: Optional[Iterable[Any]] = None, *, exception: Optional[Exception] = None
    ) -> None:
        self.chunks = list(chunks) if chunks is not None else []
        self.exception = exception
        self.calls: list[Tuple[str, Dict[str, Any], Optional[float]]] = []

    def __call__(
        self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None
    ) -> Iterator[Any]:
        self.calls.append((url, payload, timeout_s))
        if self.exception is not None:
            raise self.exception
        for chunk in self.chunks:
            yield chunk


class LLMClientStreamTests(unittest.TestCase):
    def test_stream_events_sequence(self) -> None:
        """A stream of chunks should produce the correct sequence of StreamEvent objects."""
        chunks = [
            {"message": {"content": "Hel"}},
            {"message": {"content": "lo"}},
            {
                "message": {
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {"name": "get_temp", "arguments": {"city": "NY"}, "index": 0},
                        }
                    ]
                }
            },
            {"message": {"content": " world"}},
        ]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)
        events = list(
            client.chat_stream([
                {"role": "user", "content": "Hello"},
            ], model="m")
        )

        self.assertEqual(len(events), 4)
        self.assertEqual(events[0].type, "text")
        self.assertEqual(events[0].text_delta, "Hel")
        self.assertIsNone(events[0].tool_call)

        self.assertEqual(events[1].type, "text")
        self.assertEqual(events[1].text_delta, "lo")

        self.assertEqual(events[2].type, "tool_call")
        self.assertIsNotNone(events[2].tool_call)
        tc = events[2].tool_call
        assert tc is not None
        self.assertEqual(tc.name, "get_temp")
        self.assertEqual(tc.arguments, {"city": "NY"})
        self.assertEqual(tc.id, "0")

        self.assertEqual(events[3].type, "text")
        self.assertEqual(events[3].text_delta, " world")

        self.assertEqual(len(dummy_stream.calls), 1)
        url, payload, timeout = dummy_stream.calls[0]
        self.assertTrue(url.endswith("/api/chat"))
        self.assertEqual(payload["model"], "m")
        self.assertTrue(payload["stream"])
        self.assertIsNone(timeout)

    def test_chat_stream_request_includes_top_level_model_options(self) -> None:
        dummy_stream = DummyStream([{"message": {"content": "ok"}}])
        client = LLMClient(http_stream=dummy_stream)

        list(
            client.chat_stream(
                [{"role": "user", "content": "Hello"}],
                model="qwen3:8b",
                model_options={"think": False},
            )
        )

        _url, payload, _timeout = dummy_stream.calls[0]
        self.assertFalse(payload["think"])

    def test_chat_stream_collect_text_only(self) -> None:
        """Collected streaming text should return a ChatResult with assistant_message."""
        chunks = [
            {"message": {"content": "Hel"}},
            {"message": {"content": "lo"}},
            {"message": {"content": " world"}},
        ]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)

        result = client.chat_stream_collect(
            [{"role": "user", "content": "Hello"}],
            model="m",
        )

        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.tool_calls, [])
        self.assertEqual(
            result.assistant_message,
            {
                "role": "assistant",
                "content": "Hello world",
            },
        )
        self.assertEqual(len(result.raw), 3)

    def test_chat_stream_collect_tool_calls(self) -> None:
        """Collected streaming tool calls should produce normalized assistant_message."""
        chunks = [
            {
                "message": {
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": {"city": "Orlando"},
                            },
                        }
                    ]
                }
            }
        ]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)

        result = client.chat_stream_collect(
            [{"role": "user", "content": "weather?"}],
            model="m",
        )

        self.assertEqual(result.text, "")
        self.assertEqual(len(result.tool_calls), 1)

        call = result.tool_calls[0]
        self.assertEqual(call.name, "get_weather")
        self.assertEqual(call.arguments, {"city": "Orlando"})
        self.assertTrue(call.id)

        assistant_message = result.assistant_message
        self.assertEqual(assistant_message["role"], "assistant")
        self.assertEqual(assistant_message["content"], "")
        self.assertIn("tool_calls", assistant_message)
        self.assertEqual(len(assistant_message["tool_calls"]), 1)

        tc = assistant_message["tool_calls"][0]
        self.assertEqual(tc["name"], "get_weather")
        self.assertEqual(tc["arguments"], {"city": "Orlando"})
        self.assertTrue(tc["id"])

    def test_chat_stream_collect_text_and_tool_calls(self) -> None:
        """Collected streaming result should preserve both text and normalized tool calls."""
        chunks = [
            {"message": {"content": "Let me check."}},
            {
                "message": {
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": {"city": "Orlando"},
                                "index": 0,
                            },
                        }
                    ]
                }
            },
        ]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)

        result = client.chat_stream_collect(
            [{"role": "user", "content": "weather?"}],
            model="m",
        )

        self.assertEqual(result.text, "Let me check.")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].id, "0")

        assistant_message = result.assistant_message
        self.assertEqual(assistant_message["role"], "assistant")
        self.assertEqual(assistant_message["content"], "Let me check.")
        self.assertIn("tool_calls", assistant_message)
        self.assertEqual(assistant_message["tool_calls"][0]["id"], "0")

    def test_stream_connection_error(self) -> None:
        """A URLError should map to ConnectionError."""
        dummy_stream = DummyStream(exception=urlerror.URLError("fail"))
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(ConnectionError):
            list(client.chat_stream([{"role": "user", "content": "x"}], model="foo"))

    def test_stream_timeout_error(self) -> None:
        """A socket.timeout should map to TimeoutError and include the timeout value."""
        dummy_stream = DummyStream(exception=socket.timeout("timed out"))
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(TimeoutError) as ctx:
            list(
                client.chat_stream([{"role": "user", "content": "x"}], model="foo", timeout_s=3.0)
            )
        self.assertIn("3.0", str(ctx.exception))

    def test_stream_model_not_found(self) -> None:
        """A 404 HTTPError mentioning model not found should map to ModelNotFoundError."""
        exc = JSONHTTPError(404, "error: model not found")
        dummy_stream = DummyStream(exception=exc)
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(ModelNotFoundError):
            list(client.chat_stream([{"role": "user", "content": "hi"}], model="bar"))

    def test_stream_http_status_error(self) -> None:
        """Other non-200 statuses should map to HTTPStatusError."""
        exc = JSONHTTPError(500, "internal error")
        dummy_stream = DummyStream(exception=exc)
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(HTTPStatusError):
            list(client.chat_stream([{"role": "user", "content": "oops"}], model="bar"))

    def test_stream_invalid_chunk(self) -> None:
        """Invalid JSON chunks should raise LLMClientError."""
        chunks = ["not-json"]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(LLMClientError):
            list(client.chat_stream([{"role": "user", "content": "x"}], model="m"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
