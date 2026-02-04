"""Type and error definitions for the LLMClient module.

The LLMClient core abstracts network interactions behind a small set of
custom exception types.  These exceptions are used to communicate
meaningful error conditions up to callers without tying the API to a
specific HTTP or socket library.  Callers can catch the base
``LLMClientError`` to handle all failures generically or catch more
specific subclasses when desired.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Tuple


class LLMClientError(Exception):
    """Base class for all LLMClient‑specific errors."""


class ConnectionError(LLMClientError):
    """Raised when the client cannot connect to the Ollama server.

    This error is used for any network‑level failure such as the
    server not running, DNS resolution failures or connection refusals.
    """


class ModelNotFoundError(LLMClientError):
    """Raised when the specified model is not available locally."""


class TimeoutError(LLMClientError):
    """Raised when a request exceeds the configured timeout."""


class HTTPStatusError(LLMClientError):
    """Raised when the Ollama server returns a non‑200 status code.

    The error message will include the status code and, if available,
    a short snippet of the response body.
    """


class PostJSONCallable(Protocol):
    """Callable protocol for dependency‑injectable HTTP JSON functions.

    ``url``: the full URL to post to
    ``payload``: a JSON‑serialisable object to send as the request body
    ``timeout_s``: optional timeout in seconds

    Must return a parsed JSON object (typically a dict) on success or
    raise an exception on failure.
    """

    def __call__(self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Any:
        ...
        
