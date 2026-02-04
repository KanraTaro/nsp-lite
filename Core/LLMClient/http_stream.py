"""Streaming HTTP helper for posting JSON without third‑party dependencies.

This module provides a minimal helper for performing HTTP POST
requests that return a stream of JSON objects.  It is similar in
spirit to ``Core.LLMClient.http_json`` but yields parsed JSON
objects incrementally rather than loading the entire response into
memory.

The helper defined here is dependency‑injectable so that unit tests
can substitute a deterministic generator without performing any real
network I/O.  See ``Core/LLMClient/types.py`` for the
``StreamJSONCallable`` protocol.
"""

from __future__ import annotations

import json
import socket
from typing import Any, Dict, Iterator, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

from .http_json import HTTPError as _HTTPError


def stream_json(url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Iterator[Any]:
    """Post JSON to ``url`` and yield a stream of parsed JSON objects.

    This helper sends a POST request with a JSON body and then yields
    each line of the response decoded as JSON.  It assumes the
    server emits newline‑delimited JSON (NDJSON) or chunked JSON
    objects separated by newlines.  Blank lines are skipped.  The
    caller is responsible for catching exceptions and mapping them
    into higher level error types.

    Parameters:
        url: Full URL to send the request to
        payload: JSON‑serialisable request body
        timeout_s: Optional timeout in seconds

    Yields:
        Parsed JSON objects (typically dictionaries) from the response

    Raises:
        HTTPError: if the server returns a non‑200 status code
        URLError: for connection issues such as DNS failures or
            connection refusals
        socket.timeout: if the request times out
        ValueError: if a response chunk cannot be parsed as JSON
    """
    data: bytes = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        resp = urlrequest.urlopen(req, timeout=timeout_s)  # type: ignore[attr-defined]
    except urlerror.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = str(exc)
        snippet = body_text[:200]
        raise _HTTPError(status, snippet) from exc
    except urlerror.URLError as exc:
        raise exc

    try:
        for raw_line in resp:  # type: ignore[assignment]
            try:
                line_str: str = raw_line.decode("utf-8", errors="replace")
            except Exception:
                # skip undecodable binary noise
                continue
            line_str = line_str.strip()
            if not line_str:
                continue
            try:
                yield json.loads(line_str)
            except Exception as exc:
                raise ValueError("Response chunk is not valid JSON") from exc
    finally:
        try:
            resp.close()  # type: ignore[call-arg]
        except Exception:
            pass
