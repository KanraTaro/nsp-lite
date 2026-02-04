"""Minimal HTTP helper for posting JSON without third‑party dependencies.

This helper uses the Python standard library to perform a JSON POST
request and return the parsed JSON response.  It raises a custom
``HTTPError`` when the server responds with a non‑200 status code and
propagates network‑level exceptions (e.g. ``URLError`` or
``socket.timeout``) directly.  Callers are expected to catch these
exceptions and map them into higher level error types as appropriate.
"""

from __future__ import annotations

import json
from http.client import HTTPResponse
from typing import Any, Dict, Optional
from urllib import error as urlerror
from urllib import request as urlrequest


class HTTPError(Exception):
    """Raised when an HTTP response status is not 200.

    The ``status_code`` attribute stores the numeric code and ``body``
    contains the raw response body (decoded as UTF‑8) truncated to
    preserve only the first few hundred characters.  Callers may use
    this to craft user‑facing error messages.
    """

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"HTTP error {status_code}")
        self.status_code: int = status_code
        # Store a short snippet of the body to avoid huge messages
        self.body: str = body


def post_json(url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Any:
    data: bytes = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlrequest.urlopen(req, timeout=timeout_s) as resp:  # type: ignore[attr-defined]
            status: int = resp.getcode()
            body_bytes: bytes = resp.read()  # type: ignore[assignment]
            body_text: str = body_bytes.decode("utf-8", errors="replace")
    except urlerror.HTTPError as exc:
        # Non-200 responses usually land here, not as a normal response.
        status = int(getattr(exc, "code", 0) or 0)
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = str(exc)
        snippet = body_text[:200]
        raise HTTPError(status, snippet) from exc
    except urlerror.URLError as exc:
        # Connection refused, DNS, etc.
        raise exc

    if status != 200:
        snippet = body_text[:200]
        raise HTTPError(status, snippet)

    try:
        return json.loads(body_text)
    except Exception as exc:
        raise ValueError("Response is not valid JSON") from exc

