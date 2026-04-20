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
    """Base class for all LLMClient-specific errors."""


class ConnectionError(LLMClientError):
    """Raised when the client cannot connect to the Ollama server.

    This error is used for any network-level failure such as the
    server not running, DNS resolution failures or connection refusals.
    """


class ModelNotFoundError(LLMClientError):
    """Raised when the specified model is not available locally."""


class TimeoutError(LLMClientError):
    """Raised when a request exceeds the configured timeout."""


class HTTPStatusError(LLMClientError):
    """Raised when the Ollama server returns a non-200 status code.

    The error message will include the status code and, if available,
    a short snippet of the response body.
    """


class PostJSONCallable(Protocol):
    """Callable protocol for dependency-injectable HTTP JSON functions."""

    def __call__(self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Any:
        ...


class StreamJSONCallable(Protocol):
    """Callable protocol for dependency-injectable streaming JSON functions."""

    def __call__(self, url: str, payload: Dict[str, Any], *, timeout_s: Optional[float] = None) -> Iterator[Any]:
        ...


@dataclass
class Message:
    """Provider-neutral representation of a chat message."""

    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List['ToolCall']] = None


@dataclass
class ToolDef:
    """Definition of a callable tool available to the model."""

    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class ToolCall:
    """Representation of a tool call returned by the model."""

    id: Optional[str]
    name: str
    arguments: Dict[str, Any]
    arguments_json: str


@dataclass
class ChatResult:
    """Final result of a non-streaming or collected streaming chat call.

    Parameters:
        text: The assistant's final reply as a single string.
        tool_calls: A list of tool calls requested by the model. This
            list may be empty if no tool calls were produced.
        assistant_message: A normalized, provider-agnostic assistant
            message ready to append to conversation history. This will
            include either a standard assistant reply or a tool-call
            message with ``tool_calls``.
        raw: The raw response object returned by the provider. This
            is provided for debugging or advanced usage and should be
            considered opaque by most callers.
    """

    text: str
    tool_calls: List[ToolCall]
    assistant_message: Dict[str, Any]
    raw: Any


@dataclass
class StreamEvent:
    """A single incremental update from a streaming chat call."""

    type: str
    text_delta: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    raw: Any = None
