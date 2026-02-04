"""Unit tests for the LLMClient Ollama streaming chat backend.

These tests verify that the streaming logic correctly parses NDJSON
chunks into provider‑neutral ``StreamEvent`` objects and maps errors
into the appropriate exception types defined in
``Core.LLMClient.types``.  The streaming layer is mocked so that no
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

    ``chunks``: an iterable of JSON‑serialisable objects or raw JSON
        strings to yield to the client.
    ``exception``: optional exception to raise instead of returning a
        normal iterator.  When set, no chunks are yielded and the
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
        # Return an iterator over the chunks
        for chunk in self.chunks:
            yield chunk


class LLMClientStreamTests(unittest.TestCase):
    def test_stream_events_sequence(self) -> None:
        """A stream of chunks should produce the correct sequence of StreamEvent objects."""
        # Define a sequence of chunks mixing text and tool calls
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
        # Expect four events: text, text, tool_call, text
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
        # The id should be derived from index 0
        self.assertEqual(tc.id, "0")

        self.assertEqual(events[3].type, "text")
        self.assertEqual(events[3].text_delta, " world")

        # Verify only one call was recorded and payload was constructed properly
        self.assertEqual(len(dummy_stream.calls), 1)
        url, payload, timeout = dummy_stream.calls[0]
        # URL should end with /api/chat
        self.assertTrue(url.endswith("/api/chat"))
        self.assertEqual(payload["model"], "m")
        self.assertTrue(payload["stream"])  # stream must be True

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
        """Other non‑200 statuses should map to HTTPStatusError."""
        exc = JSONHTTPError(500, "internal error")
        dummy_stream = DummyStream(exception=exc)
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(HTTPStatusError):
            list(client.chat_stream([{"role": "user", "content": "oops"}], model="bar"))

    def test_stream_invalid_chunk(self) -> None:
        """Invalid JSON chunks should raise LLMClientError."""
        # Provide a chunk that is not a dict and not valid JSON string
        chunks = ["not-json"]
        dummy_stream = DummyStream(chunks)
        client = LLMClient(http_stream=dummy_stream)
        with self.assertRaises(LLMClientError):
            list(client.chat_stream([{"role": "user", "content": "x"}], model="m"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
