"""ProjectRoot package initialization.

This package exposes a minimal API for discovering the logical root of a
project at runtime.  See :mod:`ProjectRoot.skill` for the
implementation details.

Usage example::

    from ProjectRoot.skill import get_effective_root

    root = get_effective_root()
    print(f"Effective root is: {root}")

The functions defined in :mod:`ProjectRoot.skill` do not write to
disk and have no side effects beyond logging.  They rely entirely on
environment variables for configuration and are safe to call repeatedly.
"""

from .skill import find_root, get_effective_root

__all__: list[str] = ["find_root", "get_effective_root"]
