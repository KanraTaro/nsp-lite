"""High‑level API for interacting with language model backends.

The :class:`LLMClient` class provides a single method,
``generate()``, which dispatches to a configured backend to obtain a
completion for a given prompt.  The default backend is ``ollama``.

Backends are implemented in the ``Core.LLMClient.backends`` package.
Future passes may introduce additional backends (e.g. OpenAI, Hugging
Face, etc.).  The backend name may be supplied at construction time.
"""

from __future__ import annotations

from typing import Optional

from .types import PostJSONCallable


class LLMClient:
    """Client for generating completions using different backends.

    Parameters:
        backend: the name of the backend to use; currently only
            ``"ollama"`` is supported
        http_post: optional dependency‑injected HTTP JSON helper.  When
            provided it will override the default helper used by the
            backend.  This is primarily intended for unit tests.
    """

    def __init__(self, *, backend: str = "ollama", http_post: Optional[PostJSONCallable] = None) -> None:
        self.backend = backend
        self.http_post = http_post

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
            raise ValueError(f"Unsupported backend: {self.backend}")

        # Import lazily to avoid unnecessary dependencies for other backends
        from .backends.ollama import generate as ollama_generate  # type: ignore

        return ollama_generate(
            prompt,
            model=model,
            host=host,
            timeout_s=timeout_s,
            http_post=self.http_post,
        )