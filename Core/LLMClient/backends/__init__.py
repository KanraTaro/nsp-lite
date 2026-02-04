"""Backend implementations for LLMClient.

This package contains backend specific ``generate`` functions.  Each
backend must expose a ``generate`` function with the signature

``generate(prompt: str, *, model: str | None, host: str | None,
           timeout_s: float | None,
           http_post: PostJSONCallable | None) -> str``.

The function should return a plain string containing the model’s
response or raise one of the exceptions defined in
``Core.LLMClient.types``.
"""

from __future__ import annotations

__all__ = ["ollama"]