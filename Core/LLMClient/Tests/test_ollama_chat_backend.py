"""Unit tests for the LLMClient Ollama chat backend.

These tests verify that the Ollama backend constructs chat requests
correctly, parses responses into provider‑neutral types and maps
various error conditions into the public error types defined in
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
    ToolDef,
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


class LLMClientChatTests(unittest.TestCase):
    def test_chat_success(self) -> None:
        """A successful chat call should return a ChatResult and build the correct request."""
        # Response with assistant content
        dummy_resp = {
            "model": "gemma3",
            "message": {
                "role": "assistant",
                "content": "Hi there!",
            },
        }
        dummy = DummyPost(dummy_resp)
        client = LLMClient(http_post=dummy)
        messages = [
            {"role": "user", "content": "Hello?"},
        ]
        result = client.chat(
            messages,
            model="gemma3",
            host="http://example.com",
            timeout_s=5.0,
        )
        # Should return ChatResult text
        self.assertEqual(result.text, "Hi there!")
        # Should have no tool calls
        self.assertEqual(result.tool_calls, [])
        # Verify a single POST call was made
        self.assertEqual(len(dummy.calls), 1)
        url, payload, timeout = dummy.calls[0]
        self.assertEqual(url, "http://example.com/api/chat")
        # Payload should include the model name, messages list and stream flag
        self.assertEqual(payload["model"], "gemma3")
        self.assertEqual(payload["messages"], messages)
        self.assertFalse(payload["stream"])
        # Timeout should propagate
        self.assertEqual(timeout, 5.0)

    def test_chat_default_host(self) -> None:
        """If host is omitted the default base URL should be used."""
        dummy = DummyPost({"model": "x", "message": {"role": "assistant", "content": "ok"}})
        client = LLMClient(http_post=dummy)
        client.chat([{"role": "user", "content": "hi"}], model="foo")
        self.assertEqual(len(dummy.calls), 1)
        url, _, _ = dummy.calls[0]
        # default host ends with /api/chat
        self.assertTrue(url.endswith("/api/chat"))

    def test_chat_tool_call_parsing(self) -> None:
        """Tool calls in the response should be parsed into ToolCall objects."""
        dummy_resp = {
            "model": "m",
            "message": {
                "role": "assistant",
                "content": "Here is the weather.",
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "index": 0,
                            "arguments": {"city": "NY"},
                        },
                    }
                ],
            },
        }
        dummy = DummyPost(dummy_resp)
        client = LLMClient(http_post=dummy)
        result = client.chat([{"role": "user", "content": "weather?"}], model="m")
        self.assertEqual(result.text, "Here is the weather.")
        # One tool call should be returned
        self.assertEqual(len(result.tool_calls), 1)
        call = result.tool_calls[0]
        self.assertEqual(call.id, "0")
        self.assertEqual(call.name, "get_weather")
        self.assertEqual(call.arguments, {"city": "NY"})
        # Arguments JSON should be canonical
        self.assertIn('"city":"NY"', call.arguments_json)

    def test_chat_request_includes_tools(self) -> None:
        """Supplying tools should include them in the request payload."""
        dummy = DummyPost({"model": "m", "message": {"role": "assistant", "content": "ok"}})
        client = LLMClient(http_post=dummy)
        tools = [
            ToolDef(
                name="get_temp",
                description="Get temperature",
                parameters={"type": "object", "properties": {}, "required": []},
            )
        ]
        client.chat([{"role": "user", "content": "temp?"}], model="m", tools=tools)
        # Verify tools presence in payload
        self.assertEqual(len(dummy.calls), 1)
        _, payload, _ = dummy.calls[0]
        self.assertIn("tools", payload)
        tools_payload = payload["tools"]
        self.assertIsInstance(tools_payload, list)
        self.assertEqual(tools_payload[0]["type"], "function")
        self.assertEqual(tools_payload[0]["function"]["name"], "get_temp")

    def test_chat_connection_error(self) -> None:
        """Network errors should map to ConnectionError."""
        dummy = DummyPost(exception=urlerror.URLError("boom"))
        client = LLMClient(http_post=dummy)
        with self.assertRaises(ConnectionError) as ctx:
            client.chat([{"role": "user", "content": "test"}], model="foo")
        self.assertIn("Ollama not running or host unreachable", str(ctx.exception))

    def test_chat_timeout_error(self) -> None:
        """Socket timeouts should map to TimeoutError and include the timeout value."""
        dummy = DummyPost(exception=socket.timeout("timed out"))
        client = LLMClient(http_post=dummy)
        with self.assertRaises(TimeoutError) as ctx:
            client.chat([{"role": "user", "content": "test"}], model="foo", timeout_s=2.5)
        self.assertIn("2.5", str(ctx.exception))

    def test_chat_model_not_found(self) -> None:
        """A 404 error mentioning model not found should map to ModelNotFoundError."""
        exc = JSONHTTPError(404, "error: model not found")
        dummy = DummyPost(exception=exc)
        client = LLMClient(http_post=dummy)
        with self.assertRaises(ModelNotFoundError):
            client.chat([{"role": "user", "content": "hi"}], model="bar")

    def test_chat_http_status_error(self) -> None:
        """Other non‑200 statuses should map to HTTPStatusError."""
        exc = JSONHTTPError(500, "internal error")
        dummy = DummyPost(exception=exc)
        client = LLMClient(http_post=dummy)
        with self.assertRaises(HTTPStatusError) as ctx:
            client.chat([{"role": "user", "content": "oops"}], model="bar")
        msg = str(ctx.exception)
        self.assertIn("500", msg)
        self.assertIn("internal error", msg)

    def test_chat_invalid_response(self) -> None:
        """Responses lacking a 'message' key should raise LLMClientError."""
        dummy = DummyPost({"foo": "bar"})
        client = LLMClient(http_post=dummy)
        with self.assertRaises(LLMClientError):
            client.chat([{"role": "user", "content": "something"}], model="baz")

    def test_chat_missing_model_argument(self) -> None:
        """Calling chat without specifying a model should raise LLMClientError."""
        dummy = DummyPost({"model": "ignored", "message": {"content": "ignored"}})
        client = LLMClient(http_post=dummy)
        with self.assertRaises(LLMClientError):
            client.chat([{"role": "user", "content": "anything"}], model=None)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
