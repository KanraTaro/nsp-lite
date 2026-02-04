from __future__ import annotations

import os
import unittest

from Core.LLMClient.client import LLMClient


class OllamaIntegrationTests(unittest.TestCase):
    def test_generate_live_ollama(self) -> None:
        if os.environ.get("NSPL_RUN_OLLAMA_INTEGRATION", "").lower() not in ("1", "true", "yes"):
            self.skipTest("Set NSPL_RUN_OLLAMA_INTEGRATION=1 and NSPL_OLLAMA_MODEL=qwen3:0.6b (optional NSPL_OLLAMA_HOST=http://localhost:11434) to run.")

        model = os.environ.get("NSPL_OLLAMA_MODEL", "qwen3:0.6b")
        host = os.environ.get("NSPL_OLLAMA_HOST", "http://localhost:11434")

        client = LLMClient()
        text = client.generate("Say hello in one short sentence.", model=model, host=host, timeout_s=20.0)

        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 0)


if __name__ == "__main__":
    unittest.main()

