"""Type and error definitions for the LLMClient module.

The LLMClient core abstracts network interactions behind a small set of
custom exception types.  These exceptions are used to communicate
meaningful error conditions up to callers without tying the API to a
specific HTTP or socket library.  Callers can catch the base
``LLMClientError`` to handle all failures generically or catch more
specific subclasses when desired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple


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


class StreamJSONCallable(Protocol):
    """Callable protocol for dependency‑injectable streaming JSON functions.

    A streaming callable posts a JSON payload to the given URL and
    returns an iterator over parsed JSON objects (typically
    dictionaries) yielded from the server in a chunked or NDJSON
    format.  Each yielded object corresponds to a single message
    chunk in the streamed response.  This protocol allows unit
    tests to substitute a deterministic generator without performing
    any real network I/O.

    ``url``: the full URL to post to
    ``payload``: a JSON‑serialisable object to send as the request body
    ``timeout_s``: optional timeout in seconds

    Must yield parsed JSON objects on success or raise an exception on failure.
    """

    def __call__(self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Iterator[Any]:
        ...


@dataclass
class Message:
    """Provider‑neutral representation of a chat message.

    Parameters:
        role: The role of the sender (e.g. ``"user"``, ``"assistant"``,
            ``"system"`` or ``"tool"``).
        content: The textual content of the message.  For tool messages
            this typically contains the tool result.  May be ``None``
            if the message conveys only a tool call.
        name: Optional identifier for the message sender.  For tool
            messages this should match the tool's name.
        tool_calls: Optional list of tool calls associated with this
            message.  This field is used when the assistant returns one
            or more tool call requests.
    """

    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List['ToolCall']] = None


@dataclass
class ToolDef:
    """Definition of a callable tool available to the model.

    Parameters:
        name: The name by which the model will refer to the tool.
        description: A short human readable description of what the tool does.
        parameters: A JSON schema describing the expected input arguments
            for the tool.  It must be a valid JSON schema object with
            ``type``, ``properties`` and ``required`` fields as needed.
    """

    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class ToolCall:
    """Representation of a tool call returned by the model.

    Parameters:
        id: A unique identifier for the call within the current chat.
            If the provider does not supply an identifier, the index
            within the returned list is used and converted to a string.
        name: The name of the tool being called.
        arguments: The arguments for the tool as a dictionary.
        arguments_json: A canonical JSON string representation of the
            arguments.  Whitespace is minimised and keys are sorted to
            ensure reproducibility.
    """

    id: Optional[str]
    name: str
    arguments: Dict[str, Any]
    arguments_json: str


@dataclass
class ChatResult:
    """Final result of a non‑streaming chat call.

    Parameters:
        text: The assistant's final reply as a single string.
        tool_calls: A list of tool calls requested by the model.  This
            list may be empty if no tool calls were produced.
        raw: The raw response object returned by the provider.  This
            is provided for debugging or advanced usage and should be
            considered opaque by most callers.
    """

    text: str
    tool_calls: List[ToolCall]
    raw: Any


@dataclass
class StreamEvent:
    """A single incremental update from a streaming chat call.

    Parameters:
        type: The type of event.  Currently ``"text"`` indicates a
            partial textual delta and ``"tool_call"`` indicates a new
            tool call encountered in the stream.
        text_delta: The incremental text produced by the model.  Only
            present when ``type`` is ``"text"``.
        tool_call: The tool call associated with this event.  Only
            present when ``type`` is ``"tool_call"``.
        raw: The raw chunk returned by the provider for this event.
    """

    type: str
    text_delta: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    raw: Any = None
        
