"""Ollama backend implementation for LLMClient.

This module defines a ``generate`` function that wraps the Ollama
``/api/generate`` endpoint. It builds the request payload, sends the
request using an injectable HTTP JSON helper and returns the
``response`` field of the JSON reply.

Errors raised by the underlying HTTP helper are mapped into the custom
exception types defined in ``Core.LLMClient.types``. See the
documentation in ``Core/LLMClient/README.md`` for details.
"""

from __future__ import annotations

import json
import socket
import uuid
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


DEFAULT_HOST: str = "http://localhost:11434"


def _build_chat_url(host: str) -> str:
    """Return the full chat endpoint URL given a base host."""
    host = host.rstrip("/")
    return f"{host}/api/chat"


def _build_url(host: str) -> str:
    """Return the full generate endpoint URL given a base host."""
    host = host.rstrip("/")
    return f"{host}/api/generate"


def _apply_model_options(payload: Dict[str, Any], model_options: Optional[Dict[str, Any]]) -> None:
    if not isinstance(model_options, dict):
        return
    for key, value in model_options.items():
        cleaned_key = str(key or "").strip()
        if cleaned_key == "":
            continue
        payload[cleaned_key] = value


def _normalize_tool_call_id(
    *,
    call: Optional[Dict[str, Any]] = None,
    func: Optional[Dict[str, Any]] = None,
    fallback_index: Optional[int] = None,
) -> str:
    """Return a stable, non-empty tool call id."""
    call = call or {}
    func = func or {}

    call_id = call.get("id")
    if isinstance(call_id, str) and call_id.strip() != "":
        return call_id

    func_id = func.get("id")
    if isinstance(func_id, str) and func_id.strip() != "":
        return func_id

    func_index = func.get("index")
    if isinstance(func_index, int):
        return str(func_index)

    call_index = call.get("index")
    if isinstance(call_index, int):
        return str(call_index)

    if fallback_index is not None:
        return f"call_{fallback_index}"

    return f"call_{uuid.uuid4().hex[:12]}"


def _build_assistant_message(text: str, tool_calls: list[Any]) -> Dict[str, Any]:
    """Build a normalized assistant history message."""
    message: Dict[str, Any] = {
        "role": "assistant",
        "content": text if text is not None else "",
    }

    if tool_calls:
        normalized_calls: list[Dict[str, Any]] = []
        for tc in tool_calls:
            if isinstance(tc, dict):
                tc_id = str(tc.get("id", "")).strip() or f"call_{uuid.uuid4().hex[:12]}"
                tc_name = str(tc.get("name", "")).strip()
                tc_arguments = tc.get("arguments") or {}
            else:
                raw_id = getattr(tc, "id", None)
                tc_id = str(raw_id).strip() if raw_id is not None else ""
                if tc_id == "":
                    tc_id = f"call_{uuid.uuid4().hex[:12]}"
                tc_name = str(getattr(tc, "name", "") or "").strip()
                tc_arguments = getattr(tc, "arguments", {}) or {}

            normalized_calls.append(
                {
                    "id": tc_id,
                    "name": tc_name,
                    "arguments": tc_arguments,
                }
            )

        message["tool_calls"] = normalized_calls

    return message


def generate(
    prompt: str,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    model_options: Optional[Dict[str, Any]] = None,
    http_post: Optional[PostJSONCallable] = None,
) -> str:
    """Generate a completion for ``prompt`` using the Ollama API."""
    if model is None or not str(model).strip():
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
    _apply_model_options(payload, model_options)

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

    if isinstance(result, dict) and "response" in result:
        response = result.get("response")
        return str(response) if response is not None else ""

    raise LLMClientError("Invalid response from Ollama: missing 'response' field")


def _convert_messages(messages: Any) -> list[Dict[str, Any]]:
    """Convert message history into Ollama request dictionaries.

    Supports:
    - plain dict messages
    - provider-neutral Message objects
    - object-style ToolCall entries
    - normalized dict-style assistant tool_calls
    - normalized dict-style tool result messages
    """
    if messages is None:
        return []

    converted: list[Dict[str, Any]] = []

    for m in messages:
        if isinstance(m, dict):
            role = m.get("role")
            msg_dict: Dict[str, Any] = {}

            if role is not None:
                msg_dict["role"] = role

            if "content" in m:
                msg_dict["content"] = m.get("content")

            if role == "tool":
                tool_name = m.get("tool_name")
                if tool_name is None:
                    tool_name = m.get("name")
                if tool_name is not None:
                    msg_dict["tool_name"] = tool_name
            else:
                name = m.get("name")
                if name is not None:
                    msg_dict["name"] = name

            tool_calls = m.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                tc_list: list[Dict[str, Any]] = []

                for tc in tool_calls:
                    if isinstance(tc, dict):
                        tc_name = tc.get("name")
                        tc_arguments = tc.get("arguments") or {}
                        tc_id = tc.get("id")
                    else:
                        tc_name = getattr(tc, "name", None)
                        tc_arguments = getattr(tc, "arguments", {}) or {}
                        tc_id = getattr(tc, "id", None)

                    func_dict: Dict[str, Any] = {
                        "name": tc_name,
                        "arguments": tc_arguments,
                    }

                    try:
                        idx_int = int(tc_id) if tc_id is not None else None
                    except Exception:
                        idx_int = None

                    call: Dict[str, Any] = {"type": "function", "function": func_dict}
                    if idx_int is not None:
                        call["function"]["index"] = idx_int

                    tc_list.append(call)

                msg_dict["tool_calls"] = tc_list

            converted.append(msg_dict)
            continue

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
    """Convert a list of ToolDef objects into Ollama's expected schema."""
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
    model_options: Optional[Dict[str, Any]] = None,
    http_post: Optional[PostJSONCallable] = None,
) -> "ChatResult":
    """Send a chat conversation to the Ollama API and return the final reply."""
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
    _apply_model_options(payload, model_options)

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
    if not isinstance(message_obj, dict):
        raise LLMClientError("Invalid response from Ollama: malformed 'message' field")

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
            call_id = _normalize_tool_call_id(call=call, func=func, fallback_index=idx)

            try:
                args_json = json.dumps(args_dict, separators=(",", ":"), sort_keys=True)
            except Exception:
                args_json = str(args_dict)

            tc = ToolCall(
                id=call_id,
                name=str(name) if name else "",
                arguments=args_dict,
                arguments_json=args_json,
            )
            tool_calls_out.append(tc)

    assistant_message = _build_assistant_message(text, tool_calls_out)
    return ChatResult(
        text=text,
        tool_calls=tool_calls_out,
        assistant_message=assistant_message,
        raw=result,
    )


def chat_stream(
    messages: Any,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout_s: Optional[float] = None,
    tools: Optional[list[Any]] = None,
    tool_choice: Optional[str] = None,
    model_options: Optional[Dict[str, Any]] = None,
    http_post: Optional[PostJSONCallable] = None,
    http_stream: Optional[Any] = None,
) -> Iterator["StreamEvent"]:
    """Stream a chat conversation via the Ollama API."""
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
    _apply_model_options(payload, model_options)

    tool_payload = _convert_tools(tools)
    if tool_payload:
        payload["tools"] = tool_payload
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice

    stream_func = http_stream or default_stream_json

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

    try:
        for chunk in iterator:
            if not isinstance(chunk, dict):
                try:
                    chunk_dict = json.loads(chunk)  # type: ignore[arg-type]
                except Exception:
                    raise LLMClientError("Failed to parse JSON chunk from Ollama")
                chunk = chunk_dict  # type: ignore[assignment]

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
                    call_id = _normalize_tool_call_id(call=call, func=func, fallback_index=idx)

                    try:
                        args_json = json.dumps(args_dict, separators=(",", ":"), sort_keys=True)
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
