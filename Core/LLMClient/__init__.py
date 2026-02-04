"""Top‑level package for the LLMClient core module.

This package exposes the primary :class:`LLMClient` entry point and
re‑exports the public exception types for convenience.  The module
version is recorded in ``__nsp_module_version__`` for compatibility
with the NSP Lite framework.
"""

from __future__ import annotations

__nsp_module_name__ = "LLMClient"
__nsp_module_version__ = "0.1.0"

from .client import LLMClient  # noqa: F401
from .types import (
    LLMClientError,
    ConnectionError,
    ModelNotFoundError,
    TimeoutError,
    HTTPStatusError,
)

__all__ = [
    "LLMClient",
    "LLMClientError",
    "ConnectionError",
    "ModelNotFoundError",
    "TimeoutError",
    "HTTPStatusError",
]