"""Ollama backend implementation for LLMClient.

This module defines a ``generate`` function that wraps the Ollama
``/api/generate`` endpoint.  It builds the request payload, sends the
request using an injectable HTTP JSON helper and returns the
``response`` field of the JSON reply.

Errors raised by the underlying HTTP helper are mapped into the custom
exception types defined in ``Core.LLMClient.types``.  See the
documentation in ``Core/LLMClient/README.md`` for details.
"""

from __future__ import annotations

import socket
from typing import Optional

from urllib import error as urlerror

from ..http_json import HTTPError as _HTTPError, post_json as _post_json
from ..types import (
    PostJSONCallable,
    LLMClientError,
    ConnectionError,
    ModelNotFoundError,
    TimeoutError,
    HTTPStatusError,
)


# Default base URL for a local Ollama instance
DEFAULT_HOST: str = "http://localhost:11434"


def _build_url(host: str) -> str:
    """Return the full generate endpoint URL given a base host."""
    # Ensure there is exactly one slash between host and path
    host = host.rstrip("/")
    return f"{host}/api/generate"


def generate(
    prompt: str,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    http_post: Optional[PostJSONCallable] = None,
) -> str:
    """Generate a completion for ``prompt`` using the Ollama API.

    Parameters:
        prompt: the text prompt to send to the model
        model: the model name; must correspond to a locally pulled model
        host: base URL of the Ollama server; defaults to ``DEFAULT_HOST``
        timeout_s: optional timeout in seconds for the request
        http_post: dependency‑injected HTTP JSON helper; defaults to
            :func:`Core.LLMClient.http_json.post_json`

    Returns:
        The generated text contained in the ``response`` field of the
        JSON reply.

    Raises:
        ConnectionError: if the server is unreachable
        ModelNotFoundError: if the model is missing locally
        TimeoutError: if the request exceeds ``timeout_s``
        HTTPStatusError: if the server returns a non‑200 status code
        LLMClientError: for any other unexpected condition
    """

    if model is None or not str(model).strip():
        # No hard coded default; require caller to supply a model
        raise LLMClientError(
            "No model specified; pass a model name via the --model flag or the model argument"
        )
    base: str = host or DEFAULT_HOST
    url: str = _build_url(base)
    payload = {
        "model": str(model),
        "prompt": str(prompt) if prompt is not None else "",
        "stream": False,
    }

    # Choose the provided HTTP helper or fall back to the default
    post: PostJSONCallable = http_post or _post_json
    try:
        result = post(url, payload, timeout_s=timeout_s)

    except socket.timeout as exc:
        # socket.timeout signals a timeout at the socket layer
        raise TimeoutError(
            f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
        ) from exc

    except urlerror.URLError as exc:
        # Some timeouts surface as URLError(reason=socket.timeout(...))
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise TimeoutError(
                f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
            ) from exc

        # Anything else here is connection-ish (refused, DNS, etc.)
        raise ConnectionError("Ollama not running or host unreachable") from exc

    except _HTTPError as exc:
        # Non‑200 status codes; check for model not found
        body_lower = exc.body.lower() if isinstance(exc.body, str) else ""
        if "model" in body_lower and "not" in body_lower and "found" in body_lower:
            raise ModelNotFoundError(
                f"Model not available locally; run: ollama pull {model}"
            ) from exc
        # Otherwise propagate as generic HTTP status error
        raise HTTPStatusError(
            f"Ollama server returned status {exc.status_code}: {exc.body}"
        ) from exc
    except ValueError as exc:
        # JSON decode error
        raise LLMClientError("Failed to parse JSON response from Ollama") from exc
    except Exception as exc:
        # Catch all other exceptions and wrap them in LLMClientError
        raise LLMClientError(str(exc)) from exc

    # Expect a dict with a 'response' field
    if isinstance(result, dict) and "response" in result:
        response = result.get("response")
        # Some models return empty string on done; ensure string type
        return str(response) if response is not None else ""
    # Unexpected structure
    raise LLMClientError("Invalid response from Ollama: missing 'response' field")

