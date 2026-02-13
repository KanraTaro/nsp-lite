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
from typing import Any, Dict, Iterator, Optional

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


def _build_chat_url(host: str) -> str:
    """Return the full chat endpoint URL given a base host.

    Ensures there is exactly one slash between the host and the path.
    """
    host = host.rstrip("/")
    return f"{host}/api/chat"


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


def _convert_messages(messages: Any) -> list[Dict[str, Any]]:
    """Convert a list of messages or message‑like objects into dictionaries.

    Accepts a list of plain dictionaries, provider‑neutral ``Message``
    instances or objects with ``role`` and ``content`` attributes.  Returns
    a list of dictionaries suitable for sending to the Ollama API.  Tool
    call information on assistant messages is preserved if present.
    """
    if messages is None:
        return []
    converted: list[Dict[str, Any]] = []
    for m in messages:
        if isinstance(m, dict):
            converted.append(dict(m))
            continue
        # Fallback to attribute access
        role = getattr(m, "role", None)
        content = getattr(m, "content", None)
        name = getattr(m, "name", None)
        tool_calls = getattr(m, "tool_calls", None)
        msg_dict: Dict[str, Any] = {}
        if role is not None:
            msg_dict["role"] = role
        if content is not None:
            msg_dict["content"] = content
        if name:
            if role == "tool":
                msg_dict["tool_name"] = name
            else:
                msg_dict["name"] = name
        if tool_calls:
            tc_list: list[Dict[str, Any]] = []
            for tc in tool_calls:
                func_dict: Dict[str, Any] = {
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                # Try to preserve index if id is numeric
                try:
                    idx_int = int(tc.id) if tc.id is not None else None
                except Exception:
                    idx_int = None
                call: Dict[str, Any] = {"type": "function", "function": func_dict}
                if idx_int is not None:
                    call["function"]["index"] = idx_int
                tc_list.append(call)
            msg_dict["tool_calls"] = tc_list
        converted.append(msg_dict)
    return converted


def _convert_tools(tools: Any) -> list[Dict[str, Any]]:
    """Convert a list of ``ToolDef`` objects into Ollama's expected schema."""
    if not tools:
        return []
    converted: list[Dict[str, Any]] = []
    for t in tools:
        if isinstance(t, dict):
            converted.append(dict(t))
            continue
        name = getattr(t, "name", None)
        description = getattr(t, "description", "")
        parameters = getattr(t, "parameters", {})
        if name is None:
            continue
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
    return converted


def chat(
    messages: Any,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    tools: Optional[list[Any]] = None,
    tool_choice: Optional[str] = None,
    http_post: Optional[PostJSONCallable] = None,
) -> "ChatResult":
    """Send a chat conversation to the Ollama API and return the final reply.

    The ``messages`` argument must be a list of message dictionaries or
    provider‑neutral ``Message`` instances.  The model name must be
    specified.  Tools and tool_choice are optional and will be
    propagated to the backend.
    """
    from ..types import ChatResult, ToolCall, LLMClientError  # type: ignore

    if model is None or not str(model).strip():
        raise LLMClientError(
            "No model specified; pass a model name via the --model flag or the model argument"
        )

    base: str = host or DEFAULT_HOST
    url: str = _build_chat_url(base)
    payload: Dict[str, Any] = {
        "model": str(model),
        "messages": _convert_messages(messages),
        "stream": False,
    }
    tool_payload = _convert_tools(tools)
    if tool_payload:
        payload["tools"] = tool_payload
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice

    post: PostJSONCallable = http_post or _post_json
    try:
        result = post(url, payload, timeout_s=timeout_s)
    except socket.timeout as exc:
        raise TimeoutError(
            f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
        ) from exc
    except urlerror.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise TimeoutError(
                f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
            ) from exc
        raise ConnectionError("Ollama not running or host unreachable") from exc
    except _HTTPError as exc:
        body_lower = exc.body.lower() if isinstance(exc.body, str) else ""
        if "model" in body_lower and "not" in body_lower and "found" in body_lower:
            raise ModelNotFoundError(
                f"Model not available locally; run: ollama pull {model}"
            ) from exc
        raise HTTPStatusError(
            f"Ollama server returned status {exc.status_code}: {exc.body}"
        ) from exc
    except ValueError as exc:
        raise LLMClientError("Failed to parse JSON response from Ollama") from exc
    except Exception as exc:
        raise LLMClientError(str(exc)) from exc

    if not isinstance(result, dict) or "message" not in result:
        raise LLMClientError("Invalid response from Ollama: missing 'message' field")
    message_obj = result.get("message") or {}
    content = message_obj.get("content")
    text: str = str(content) if content is not None else ""
    tool_calls_out: list[ToolCall] = []
    tool_calls_in = message_obj.get("tool_calls") or []
    if isinstance(tool_calls_in, list):
        for idx, call in enumerate(tool_calls_in):
            try:
                func = call.get("function", {})
            except AttributeError:
                func = {}
            name = func.get("name")
            args_dict = func.get("arguments") or {}
            # Determine identifier
            call_id: Optional[str] = None
            if isinstance(call.get("id"), str):
                call_id = call.get("id")
            elif isinstance(func.get("id"), str):
                call_id = func.get("id")
            else:
                if isinstance(func.get("index"), int):
                    call_id = str(func.get("index"))
                elif isinstance(call.get("index"), int):
                    call_id = str(call.get("index"))
                else:
                    call_id = str(idx)
            import json as _json
            try:
                args_json = _json.dumps(args_dict, separators=(",", ":"), sort_keys=True)
            except Exception:
                args_json = str(args_dict)
            tc = ToolCall(id=call_id, name=str(name) if name else "", arguments=args_dict, arguments_json=args_json)
            tool_calls_out.append(tc)
    return ChatResult(text=text, tool_calls=tool_calls_out, raw=result)


def chat_stream(
    messages: Any,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    tools: Optional[list[Any]] = None,
    tool_choice: Optional[str] = None,
    http_post: Optional[PostJSONCallable] = None,
    http_stream: Optional[Any] = None,
) -> Iterator["StreamEvent"]:
    """Stream a chat conversation via the Ollama API.

    Returns an iterator over ``StreamEvent`` objects.  Each event
    represents either an incremental text delta or a tool call returned
    by the model.  Errors are mapped into the appropriate exception
    types defined in ``Core.LLMClient.types``.
    """
    from ..types import StreamEvent, ToolCall, LLMClientError  # type: ignore
    from ..http_stream import stream_json as default_stream_json
    if model is None or not str(model).strip():
        raise LLMClientError(
            "No model specified; pass a model name via the --model flag or the model argument"
        )
    base: str = host or DEFAULT_HOST
    url: str = _build_chat_url(base)
    payload: Dict[str, Any] = {
        "model": str(model),
        "messages": _convert_messages(messages),
        "stream": True,
    }
    tool_payload = _convert_tools(tools)
    if tool_payload:
        payload["tools"] = tool_payload
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice
    stream_func = http_stream or default_stream_json
    # Acquire iterator
    try:
        iterator = stream_func(url, payload, timeout_s=timeout_s)
    except socket.timeout as exc:
        raise TimeoutError(
            f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
        ) from exc
    except urlerror.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise TimeoutError(
                f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
            ) from exc
        raise ConnectionError("Ollama not running or host unreachable") from exc
    except _HTTPError as exc:
        body_lower = exc.body.lower() if isinstance(exc.body, str) else ""
        if "model" in body_lower and "not" in body_lower and "found" in body_lower:
            raise ModelNotFoundError(
                f"Model not available locally; run: ollama pull {model}"
            ) from exc
        raise HTTPStatusError(
            f"Ollama server returned status {exc.status_code}: {exc.body}"
        ) from exc
    except ValueError as exc:
        raise LLMClientError("Failed to parse JSON response from Ollama") from exc
    except Exception as exc:
        raise LLMClientError(str(exc)) from exc

    # Iterate through chunks, mapping errors during iteration
    try:
        for chunk in iterator:
            if not isinstance(chunk, dict):
                try:
                    import json as _json
                    chunk_dict = _json.loads(chunk)  # type: ignore
                except Exception:
                    raise LLMClientError("Failed to parse JSON chunk from Ollama")
                chunk = chunk_dict  # type: ignore
            message_obj = chunk.get("message", chunk)
            if not isinstance(message_obj, dict):
                continue
            content = message_obj.get("content")
            if isinstance(content, str):
                if content != "":
                    yield StreamEvent(type="text", text_delta=content, raw=chunk)
            elif content is not None:
                yield StreamEvent(type="text", text_delta=str(content), raw=chunk)
            tool_calls_in = message_obj.get("tool_calls") or []
            if isinstance(tool_calls_in, list) and tool_calls_in:
                for idx, call in enumerate(tool_calls_in):
                    try:
                        func = call.get("function", {})
                    except AttributeError:
                        func = {}
                    name = func.get("name")
                    args_dict = func.get("arguments") or {}
                    call_id: Optional[str]
                    if isinstance(call.get("id"), str):
                        call_id = call.get("id")
                    elif isinstance(func.get("id"), str):
                        call_id = func.get("id")
                    else:
                        if isinstance(func.get("index"), int):
                            call_id = str(func.get("index"))
                        elif isinstance(call.get("index"), int):
                            call_id = str(call.get("index"))
                        else:
                            call_id = str(idx)
                    import json as _json
                    try:
                        args_json = _json.dumps(args_dict, separators=(",", ":"), sort_keys=True)
                    except Exception:
                        args_json = str(args_dict)
                    tc = ToolCall(
                        id=call_id,
                        name=str(name) if name else "",
                        arguments=args_dict,
                        arguments_json=args_json,
                    )
                    yield StreamEvent(type="tool_call", tool_call=tc, raw=chunk)
    except socket.timeout as exc:
        raise TimeoutError(
            f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
        ) from exc
    except urlerror.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise TimeoutError(
                f"Request timed out after {timeout_s} seconds" if timeout_s else "Request timed out"
            ) from exc
        raise ConnectionError("Ollama not running or host unreachable") from exc
    except _HTTPError as exc:
        body_lower = exc.body.lower() if isinstance(exc.body, str) else ""
        if "model" in body_lower and "not" in body_lower and "found" in body_lower:
            raise ModelNotFoundError(
                f"Model not available locally; run: ollama pull {model}"
            ) from exc
        raise HTTPStatusError(
            f"Ollama server returned status {exc.status_code}: {exc.body}"
        ) from exc
    except ValueError as exc:
        raise LLMClientError("Failed to parse JSON response from Ollama") from exc
    except Exception as exc:
        raise LLMClientError(str(exc)) from exc
