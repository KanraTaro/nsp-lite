"""Unified NSPL Entry surface.

Entry is the command spine behind the root ``nspl.py`` gateway.  In this
initial pass it routes the existing skill and GUI surfaces to their current
implementations without changing their behavior.
"""

from Core.NSPL.Entry.context import EntryContext
from Core.NSPL.Entry.entry import main

__all__: list[str] = ["EntryContext", "main"]
