"""Unit tests for the LLMClient Ollama backend.

These tests verify that the Ollama backend constructs requests
correctly, parses responses as expected and maps various error
conditions into the public error types defined in
``Core.LLMClient.types``.  The HTTP layer is mocked via a simple
callable object so that no real network requests are made.
"""

from __future__ import annotations

import socket
import unittest
from typing import Any, Dict, Optional, Tuple
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


class DummyPost:
    """Helper class to simulate an HTTP JSON POST.

    ``response``: the JSON object to return on every call.
    ``exception``: optional exception to raise instead of returning a response.
    The first attribute takes precedence when both are provided.
    """

    def __init__(self, response: Optional[Dict[str, Any]] = None, *, exception: Optional[Exception] = None) -> None:
        self.calls: list[Tuple[str, Dict[str, Any], Optional[float]]] = []
        self.response = response
        self.exception = exception

    def __call__(self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Any:
        self.calls.append((url, payload, timeout_s))
        if self.exception is not None:
            raise self.exception
        return self.response


class LLMClientOllamaTests(unittest.TestCase):
    def test_generate_success(self) -> None:
        """A successful call should return the response text and build the correct request."""
        dummy = DummyPost({"response": "Hello, world"})
        client = LLMClient(http_post=dummy)
        result = client.generate(
            "Hello",
            model="llama3.2",
            host="http://example.com",
            timeout_s=5.0,
        )
        # The result should be the response field
        self.assertEqual(result, "Hello, world")
        # Exactly one call should have been made
        self.assertEqual(len(dummy.calls), 1)
        url, payload, timeout = dummy.calls[0]
        self.assertEqual(url, "http://example.com/api/generate")
        # Payload should contain the model, prompt and stream flag
        self.assertEqual(payload["model"], "llama3.2")
        self.assertEqual(payload["prompt"], "Hello")
        self.assertFalse(payload["stream"])
        # Timeout should be passed through
        self.assertEqual(timeout, 5.0)

    def test_default_host(self) -> None:
        """If host is omitted the default base URL should be used."""
        dummy = DummyPost({"response": "OK"})
        client = LLMClient(http_post=dummy)
        client.generate("Hi", model="mistral")
        self.assertEqual(len(dummy.calls), 1)
        url, _, _ = dummy.calls[0]
        self.assertEqual(url, "http://localhost:11434/api/generate")

    def test_generate_request_includes_top_level_model_options(self) -> None:
        dummy = DummyPost({"response": "OK"})
        client = LLMClient(http_post=dummy)

        client.generate("Hi", model="gpt-oss:20b", model_options={"think": "low"})

        _url, payload, _timeout = dummy.calls[0]
        self.assertEqual(payload["think"], "low")

    def test_connection_error(self) -> None:
        """Network errors should map to ConnectionError."""
        dummy = DummyPost(exception=urlerror.URLError("boom"))
        client = LLMClient(http_post=dummy)
        with self.assertRaises(ConnectionError) as ctx:
            client.generate("test", model="foo")
        # Message should mention host unreachable
        self.assertIn("Ollama not running or host unreachable", str(ctx.exception))

    def test_timeout_error(self) -> None:
        """Socket timeouts should map to TimeoutError and include the timeout value."""
        dummy = DummyPost(exception=socket.timeout("timed out"))
        client = LLMClient(http_post=dummy)
        with self.assertRaises(TimeoutError) as ctx:
            client.generate("test", model="foo", timeout_s=2.5)
        # The message should include the timeout seconds
        self.assertIn("2.5", str(ctx.exception))

    def test_model_not_found(self) -> None:
        """A 404 error mentioning model not found should map to ModelNotFoundError."""
        # Simulate a non‑200 status with a body that contains 'model not found'
        exc = JSONHTTPError(404, "error: model not found")
        dummy = DummyPost(exception=exc)
        client = LLMClient(http_post=dummy)
        with self.assertRaises(ModelNotFoundError) as ctx:
            client.generate("hello", model="llama")
        self.assertIn("ollama pull llama", str(ctx.exception).lower())

    def test_http_status_error(self) -> None:
        """Other non‑200 statuses should map to HTTPStatusError with status code included."""
        exc = JSONHTTPError(500, "internal error")
        dummy = DummyPost(exception=exc)
        client = LLMClient(http_post=dummy)
        with self.assertRaises(HTTPStatusError) as ctx:
            client.generate("oops", model="bar")
        msg = str(ctx.exception)
        self.assertIn("500", msg)
        self.assertIn("internal error", msg)

    def test_missing_response_field(self) -> None:
        """Responses lacking a 'response' key should raise LLMClientError."""
        dummy = DummyPost({"foo": "bar"})
        client = LLMClient(http_post=dummy)
        with self.assertRaises(LLMClientError):
            client.generate("something", model="baz")

    def test_missing_model_argument(self) -> None:
        """Calling generate without specifying a model should raise LLMClientError."""
        dummy = DummyPost({"response": "ignored"})
        client = LLMClient(http_post=dummy)
        with self.assertRaises(LLMClientError):
            client.generate("anything")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
