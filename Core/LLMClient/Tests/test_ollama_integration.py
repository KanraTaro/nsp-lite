from __future__ import annotations

"""Opt‑in integration tests for the Ollama backend.

These tests verify that the LLMClient can communicate with a live
Ollama server using both the generate and chat APIs, including
streaming.  They are skipped by default and only run when the
``NSPL_RUN_OLLAMA_INTEGRATION`` environment variable is set to a
truthy value ("1", "true" or "yes").  When enabled, a running
instance of Ollama and a locally pulled model are required.  The
default model is ``qwen3:0.6b`` and the default host is
``http://localhost:11434``.  These may be overridden via the
``NSPL_OLLAMA_MODEL`` and ``NSPL_OLLAMA_HOST`` environment
variables respectively.
"""

import os
import unittest
from typing import Tuple

from Core.LLMClient.client import LLMClient


class OllamaIntegrationTests(unittest.TestCase):
    """Integration tests against a live Ollama instance."""

    def _require_integration(self) -> Tuple[str, str]:
        """Return (model, host) if integration tests are enabled or skip."""
        flag = os.environ.get("NSPL_RUN_OLLAMA_INTEGRATION", "").lower()
        if flag not in ("1", "true", "yes"):
            self.skipTest(
                "Set NSPL_RUN_OLLAMA_INTEGRATION=1 and NSPL_OLLAMA_MODEL=qwen3:0.6b"
                " (optional NSPL_OLLAMA_HOST=http://localhost:11434) to run."
            )
        model = os.environ.get("NSPL_OLLAMA_MODEL", "qwen3:0.6b")
        host = os.environ.get("NSPL_OLLAMA_HOST", "http://localhost:11434")
        return model, host

    def test_generate_live_ollama(self) -> None:
        model, host = self._require_integration()
        client = LLMClient()
        text = client.generate(
            "Say hello in one short sentence.", model=model, host=host, timeout_s=20.0
        )
        # Should return non‑empty string
        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 0)

    def test_chat_live_ollama(self) -> None:
        model, host = self._require_integration()
        client = LLMClient()
        messages = [
            {"role": "user", "content": "Say hello in one short sentence."},
        ]
        result = client.chat(messages, model=model, host=host, timeout_s=20.0)
        # Should return ChatResult with non‑empty text
        self.assertGreater(len(result.text.strip()), 0)
        # Tool calls should be a list (likely empty for simple greeting)
        self.assertIsInstance(result.tool_calls, list)

    def test_stream_live_ollama(self) -> None:
        model, host = self._require_integration()
        client = LLMClient()
        messages = [
            {"role": "user", "content": "Say hello in one short sentence."},
        ]
        events = client.chat_stream(messages, model=model, host=host, timeout_s=20.0)
        aggregated = ""
        for event in events:
            if event.type == "text" and event.text_delta:
                aggregated += event.text_delta
        # The aggregated text should be non‑empty
        self.assertGreater(len(aggregated.strip()), 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
