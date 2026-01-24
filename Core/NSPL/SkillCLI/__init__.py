"""SkillCLI package initializer.

This module exposes a convenience import for the main entry point.  While
SkillCLI can be invoked with ``python -m Core.NSPL.SkillCLI``, it may also be
imported programmatically.  Importing ``main`` from here allows unit tests
to call the CLI directly without spawning a subprocess.  The actual logic
lives in :mod:`Core.NSPL.SkillCLI.skillcli`.

Note: no behaviour should occur at import time beyond exposing the
``main`` function.  All state and heavy lifting is deferred until
``main`` is executed.
"""

from Core.NSPL.SkillCLI.skillcli import main
from Core.NSPL.SkillCLI.runtime import SkillContext, create_ctx

__all__: list[str] = [
    "main",
    "SkillContext",
    "create_ctx",
]

